package sieve

import (
	"bytes"
	"regexp"
	"strings"
)

// ToolCall represents an extracted structured tool invocation.
type ToolCall struct {
	ID        string `json:"id"`
	Name      string `json:"name"`
	Arguments string `json:"arguments"`
}

// Event represents either visible stream text or extracted tool call(s).
type Event struct {
	Content   string     `json:"content,omitempty"`
	ToolCalls []ToolCall `json:"tool_calls,omitempty"`
}

// State tracks the sliding window and Markdown fence context across streaming chunks.
type State struct {
	pending          bytes.Buffer
	capture          bytes.Buffer
	capturing        bool
	insideCodeFence  bool
	inlineCodeTicks  int
	pendingToolCalls []ToolCall
}

// NewState initializes a clean sieve state.
func NewState() *State {
	return &State{}
}

// ProcessChunk processes an incremental stream token, separating safe content,
// holding potential tool tag prefixes, and intercepting complete XML tool calls.
func ProcessChunk(s *State, chunk string, toolNames []string) []Event {
	if s == nil {
		return nil
	}
	if chunk != "" {
		s.pending.WriteString(chunk)
	}

	var events []Event
	if len(s.pendingToolCalls) > 0 {
		events = append(events, Event{ToolCalls: s.pendingToolCalls})
		s.pendingToolCalls = nil
	}

	for {
		if s.capturing {
			if s.pending.Len() > 0 {
				s.capture.WriteString(s.pending.String())
				s.pending.Reset()
			}
			prefix, calls, suffix, ready := tryConsumeToolCapture(s.capture.String(), toolNames)
			if !ready {
				break
			}
			s.capture.Reset()
			s.capturing = false
			if len(calls) > 0 {
				if prefix != "" {
					events = append(events, Event{Content: prefix})
				}
				if suffix != "" {
					s.pending.WriteString(suffix)
				}
				s.pendingToolCalls = calls
				continue
			}
			if prefix != "" {
				events = append(events, Event{Content: prefix})
			}
			if suffix != "" {
				s.pending.WriteString(suffix)
			}
			continue
		}

		pending := s.pending.String()
		if pending == "" {
			break
		}

		start := findToolTagStart(s, pending)
		if start >= 0 {
			prefix := pending[:start]
			if prefix != "" {
				s.updateCodeFenceContext(prefix)
				events = append(events, Event{Content: prefix})
			}
			s.pending.Reset()
			s.capture.WriteString(pending[start:])
			s.capturing = true
			continue
		}

		safe, hold := splitSafeContent(s, pending)
		if safe == "" {
			break
		}
		s.updateCodeFenceContext(safe)
		s.pending.Reset()
		s.pending.WriteString(hold)
		events = append(events, Event{Content: safe})
	}

	return events
}

// Flush cleanly drains any buffered content at the end of the stream.
// If buffered content failed to form a valid tool call, it is returned as plain text.
func Flush(s *State, toolNames []string) []Event {
	if s == nil {
		return nil
	}
	events := ProcessChunk(s, "", toolNames)
	if len(s.pendingToolCalls) > 0 {
		events = append(events, Event{ToolCalls: s.pendingToolCalls})
		s.pendingToolCalls = nil
	}
	if s.capturing {
		prefix, calls, suffix, ready := tryConsumeToolCapture(s.capture.String(), toolNames)
		if ready && len(calls) > 0 {
			if prefix != "" {
				events = append(events, Event{Content: prefix})
			}
			events = append(events, Event{ToolCalls: calls})
			if suffix != "" {
				events = append(events, Event{Content: suffix})
			}
		} else {
			// Unresolved capture: flush raw buffered text without swallowing
			content := s.capture.String()
			if content != "" {
				events = append(events, Event{Content: content})
			}
		}
		s.capture.Reset()
		s.capturing = false
	}
	if s.pending.Len() > 0 {
		events = append(events, Event{Content: s.pending.String()})
		s.pending.Reset()
	}
	return events
}

var (
	toolOpenRegex  = regexp.MustCompile(`<(?:tool_call|function_call|invoke)>`)
	toolCloseRegex = regexp.MustCompile(`</(?:tool_call|function_call|invoke)>`)
	toolTagPattern = regexp.MustCompile(`(?s)<(?:tool_call|function_call|invoke)>(.*?)</(?:tool_call|function_call|invoke)>`)
	xmlNameRegex   = regexp.MustCompile(`<(?:name|tool_name|function)>(.*?)</(?:name|tool_name|function)>`)
	xmlArgsRegex   = regexp.MustCompile(`(?s)<(?:parameters|arguments|args)>(.*?)</(?:parameters|arguments|args)>`)
)

func findToolTagStart(s *State, text string) int {
	if s.insideCodeFence || s.inlineCodeTicks > 0 {
		return -1
	}
	loc := toolOpenRegex.FindStringIndex(text)
	if loc == nil {
		return -1
	}
	return loc[0]
}

func splitSafeContent(s *State, text string) (safe, hold string) {
	if s.insideCodeFence || s.inlineCodeTicks > 0 {
		return text, ""
	}
	idx := strings.Index(text, "<")
	if idx >= 0 {
		return text[:idx], text[idx:]
	}
	return text, ""
}

func (s *State) updateCodeFenceContext(text string) {
	for i := 0; i < len(text); {
		if text[i] == '`' {
			run := 0
			for i+run < len(text) && text[i+run] == '`' {
				run++
			}
			if run >= 3 {
				s.insideCodeFence = !s.insideCodeFence
			} else if !s.insideCodeFence {
				if s.inlineCodeTicks == 0 {
					s.inlineCodeTicks = run
				} else if s.inlineCodeTicks == run {
					s.inlineCodeTicks = 0
				}
			}
			i += run
		} else {
			i++
		}
	}
}

func tryConsumeToolCapture(captured string, allowedTools []string) (prefix string, calls []ToolCall, suffix string, ready bool) {
	loc := toolTagPattern.FindStringIndex(captured)
	if loc == nil {
		// If an open tag exists, keep waiting for the closing tag
		if toolOpenRegex.MatchString(captured) {
			return "", nil, "", false
		}
		return captured, nil, "", true
	}

	prefix = captured[:loc[0]]
	tagBody := captured[loc[0]:loc[1]]
	suffix = captured[loc[1]:]

	// Extract tool name
	nameMatch := xmlNameRegex.FindStringSubmatch(tagBody)
	toolName := "unknown"
	if len(nameMatch) > 1 {
		toolName = strings.TrimSpace(nameMatch[1])
	}

	// Extract tool arguments
	argsMatch := xmlArgsRegex.FindStringSubmatch(tagBody)
	toolArgs := "{}"
	if len(argsMatch) > 1 {
		toolArgs = strings.TrimSpace(argsMatch[1])
	}

	call := ToolCall{
		ID:        "call_" + toolName,
		Name:      toolName,
		Arguments: toolArgs,
	}

	return prefix, []ToolCall{call}, suffix, true
}

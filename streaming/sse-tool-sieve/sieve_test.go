package sieve

import (
	"testing"
)

func TestSieve_PlainTextPassThrough(t *testing.T) {
	state := NewState()
	chunks := []string{"Hello", " world!", " This is a normal stream."}

	var out string
	for _, ch := range chunks {
		events := ProcessChunk(state, ch, nil)
		for _, e := range events {
			out += e.Content
		}
	}
	events := Flush(state, nil)
	for _, e := range events {
		out += e.Content
	}

	expected := "Hello world! This is a normal stream."
	if out != expected {
		t.Fatalf("expected %q, got %q", expected, out)
	}
}

func TestSieve_HoldAndExtractToolCall(t *testing.T) {
	state := NewState()
	chunks := []string{
		"Thinking complete. ",
		"<tool",
		"_call>\n",
		"<name>get_weather</name>\n",
		"<arguments>{\"location\":\"Beijing\"}</arguments>\n",
		"</tool_call>",
		" after call text",
	}

	var content string
	var toolCalls []ToolCall

	for _, ch := range chunks {
		events := ProcessChunk(state, ch, []string{"get_weather"})
		for _, e := range events {
			content += e.Content
			if len(e.ToolCalls) > 0 {
				toolCalls = append(toolCalls, e.ToolCalls...)
			}
		}
	}
	for _, e := range Flush(state, []string{"get_weather"}) {
		content += e.Content
		if len(e.ToolCalls) > 0 {
			toolCalls = append(toolCalls, e.ToolCalls...)
		}
	}

	// Verify no XML tags leaked to user-facing content
	if content != "Thinking complete.  after call text" {
		t.Fatalf("unexpected content output: %q", content)
	}

	// Verify tool call parsed accurately
	if len(toolCalls) != 1 {
		t.Fatalf("expected 1 tool call, got %d", len(toolCalls))
	}
	if toolCalls[0].Name != "get_weather" {
		t.Fatalf("expected tool name get_weather, got %s", toolCalls[0].Name)
	}
	if toolCalls[0].Arguments != `{"location":"Beijing"}` {
		t.Fatalf("expected arguments %s, got %s", `{"location":"Beijing"}`, toolCalls[0].Arguments)
	}
}

func TestSieve_IgnoreToolTagsInsideMarkdownCodeBlock(t *testing.T) {
	state := NewState()
	chunks := []string{
		"Here is how you format a call:\n```xml\n",
		"<tool_call>\n<name>example</name>\n</tool_call>\n",
		"```\nHope that helps!",
	}

	var content string
	var toolCalls []ToolCall

	for _, ch := range chunks {
		events := ProcessChunk(state, ch, nil)
		for _, e := range events {
			content += e.Content
			if len(e.ToolCalls) > 0 {
				toolCalls = append(toolCalls, e.ToolCalls...)
			}
		}
	}
	for _, e := range Flush(state, nil) {
		content += e.Content
		if len(e.ToolCalls) > 0 {
			toolCalls = append(toolCalls, e.ToolCalls...)
		}
	}

	// Inside markdown code fence, <tool_call> must NOT be intercepted
	if len(toolCalls) != 0 {
		t.Fatalf("expected 0 tool calls inside code fence, got %d", len(toolCalls))
	}
	if content != "Here is how you format a call:\n```xml\n<tool_call>\n<name>example</name>\n</tool_call>\n```\nHope that helps!" {
		t.Fatalf("unexpected content: %q", content)
	}
}

func TestSieve_UnclosedTagFlushRecovery(t *testing.T) {
	state := NewState()
	// Simulated incomplete/broken tag followed by EOF
	chunks := []string{"Some text before <tool_call>incomplete content"}

	var content string
	for _, ch := range chunks {
		events := ProcessChunk(state, ch, nil)
		for _, e := range events {
			content += e.Content
		}
	}
	for _, e := range Flush(state, nil) {
		content += e.Content
	}

	// Must cleanly flush back without losing any text
	expected := "Some text before <tool_call>incomplete content"
	if content != expected {
		t.Fatalf("expected text preserved: %q, got %q", expected, content)
	}
}

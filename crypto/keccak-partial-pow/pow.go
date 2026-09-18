package pow

import (
	"context"
	"encoding/base64"
	"encoding/binary"
	"encoding/hex"
	"encoding/json"
	"errors"
	"strconv"
)

// Challenge represents the payload returned by DeepSeek create_pow_challenge.
type Challenge struct {
	Algorithm  string `json:"algorithm"`
	Challenge  string `json:"challenge"`
	Salt       string `json:"salt"`
	ExpireAt   int64  `json:"expire_at"`
	Difficulty int64  `json:"difficulty"`
	Signature  string `json:"signature"`
	TargetPath string `json:"target_path"`
}

// BuildPrefix formats the fixed prefix: "<salt>_<expire_at>_".
func BuildPrefix(salt string, expireAt int64) string {
	return salt + "_" + strconv.FormatInt(expireAt, 10) + "_"
}

// SolvePow searches for a nonce in [0, difficulty) such that
// DeepSeekHashV1(prefix + str(nonce)) matches challengeHex.
//
// Performance optimizations:
// 1. Prefix is pre-absorbed into baseState outside the loop.
// 2. Number formatting operates on stack buffer [20]byte, avoiding strconv.Itoa heap allocation.
// 3. Target comparison compares four uint64 values directly without hex encoding/decoding.
func SolvePow(ctx context.Context, challengeHex, salt string, expireAt, difficulty int64) (int64, error) {
	if len(challengeHex) != 64 {
		return 0, errors.New("pow: challenge must be 64 hex characters")
	}
	target, err := hex.DecodeString(challengeHex)
	if err != nil {
		return 0, err
	}
	var ta [32]byte
	copy(ta[:], target)
	t0 := binary.LittleEndian.Uint64(ta[0:])
	t1 := binary.LittleEndian.Uint64(ta[8:])
	t2 := binary.LittleEndian.Uint64(ta[16:])
	t3 := binary.LittleEndian.Uint64(ta[24:])

	prefix := []byte(BuildPrefix(salt, expireAt))
	const rate = 136
	var baseState [25]uint64
	off := 0
	for off+rate <= len(prefix) {
		for i := 0; i < rate/8; i++ {
			baseState[i] ^= binary.LittleEndian.Uint64(prefix[off+i*8:])
		}
		keccakF23(&baseState)
		off += rate
	}
	tailLen := len(prefix) - off
	var tail [rate]byte
	copy(tail[:], prefix[off:])

	var numBuf [20]byte
	for n := int64(0); n < difficulty; n++ {
		// Periodically check context cancellation
		if n&0x3FF == 0 && ctx.Err() != nil {
			return 0, ctx.Err()
		}

		v := uint64(n)
		pos := 20
		if v == 0 {
			pos--
			numBuf[pos] = '0'
		} else {
			for v > 0 {
				pos--
				numBuf[pos] = byte('0' + v%10)
				v /= 10
			}
		}
		numLen := 20 - pos
		s := baseState
		totalTail := tailLen + numLen
		if totalTail < rate {
			var buf [rate]byte
			copy(buf[:tailLen], tail[:tailLen])
			copy(buf[tailLen:totalTail], numBuf[pos:])
			buf[totalTail] = 0x06
			buf[rate-1] |= 0x80
			for i := 0; i < rate/8; i++ {
				s[i] ^= binary.LittleEndian.Uint64(buf[i*8:])
			}
			keccakF23(&s)
		} else {
			var buf [rate]byte
			copy(buf[:tailLen], tail[:tailLen])
			copy(buf[tailLen:rate], numBuf[pos:pos+(rate-tailLen)])
			for i := 0; i < rate/8; i++ {
				s[i] ^= binary.LittleEndian.Uint64(buf[i*8:])
			}
			keccakF23(&s)
			var buf2 [rate]byte
			rem := totalTail - rate
			copy(buf2[:rem], numBuf[pos+(rate-tailLen):pos+(rate-tailLen)+rem])
			buf2[rem] = 0x06
			buf2[rate-1] |= 0x80
			for i := 0; i < rate/8; i++ {
				s[i] ^= binary.LittleEndian.Uint64(buf2[i*8:])
			}
			keccakF23(&s)
		}
		if s[0] == t0 && s[1] == t1 && s[2] == t2 && s[3] == t3 {
			return n, nil
		}
	}
	return 0, errors.New("pow: no solution found within difficulty range")
}

// BuildPowHeader packages the solution into base64(json).
func BuildPowHeader(c *Challenge, answer int64) (string, error) {
	b, err := json.Marshal(map[string]any{
		"algorithm":   c.Algorithm,
		"challenge":   c.Challenge,
		"salt":        c.Salt,
		"answer":      answer,
		"signature":   c.Signature,
		"target_path": c.TargetPath,
	})
	if err != nil {
		return "", err
	}
	return base64.StdEncoding.EncodeToString(b), nil
}

// SolveAndBuildHeader solves the challenge and returns the x-ds-pow-response header.
func SolveAndBuildHeader(ctx context.Context, c *Challenge) (string, error) {
	if c.Algorithm != "DeepSeekHashV1" {
		return "", errors.New("pow: unsupported algorithm: " + c.Algorithm)
	}
	diff := c.Difficulty
	if diff <= 0 {
		diff = 144000
	}
	ans, err := SolvePow(ctx, c.Challenge, c.Salt, c.ExpireAt, diff)
	if err != nil {
		return "", err
	}
	return BuildPowHeader(c, ans)
}

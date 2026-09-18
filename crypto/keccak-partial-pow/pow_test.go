package pow

import (
	"context"
	"encoding/hex"
	"testing"
)

func TestDeepSeekHashV1(t *testing.T) {
	input := []byte("test-data-for-deepseek-hash")
	hash := DeepSeekHashV1(input)
	if len(hash) != 32 {
		t.Fatalf("expected 32 bytes hash, got %d", len(hash))
	}
	// Verify deterministic output
	hash2 := DeepSeekHashV1(input)
	if hash != hash2 {
		t.Fatalf("expected deterministic hash output")
	}
}

func TestSolvePow_KnownTarget(t *testing.T) {
	salt := "test_salt_123"
	expireAt := int64(1750000000)
	targetNonce := int64(142)

	// Pre-generate valid challenge
	prefix := BuildPrefix(salt, expireAt)
	expectedHash := DeepSeekHashV1([]byte(prefix + "142"))
	challengeHex := hex.EncodeToString(expectedHash[:])

	ctx := context.Background()
	ans, err := SolvePow(ctx, challengeHex, salt, expireAt, 1000)
	if err != nil {
		t.Fatalf("expected solved pow, got error: %v", err)
	}
	if ans != targetNonce {
		t.Fatalf("expected answer %d, got %d", targetNonce, ans)
	}
}

func BenchmarkSolvePow(b *testing.B) {
	salt := "benchmark_salt"
	expireAt := int64(1750000000)
	prefix := BuildPrefix(salt, expireAt)
	expectedHash := DeepSeekHashV1([]byte(prefix + "500"))
	challengeHex := hex.EncodeToString(expectedHash[:])
	ctx := context.Background()

	b.ResetTimer()
	b.ReportAllocs()
	for i := 0; i < b.N; i++ {
		_, err := SolvePow(ctx, challengeHex, salt, expireAt, 600)
		if err != nil {
			b.Fatal(err)
		}
	}
}

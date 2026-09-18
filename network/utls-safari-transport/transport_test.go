package transport

import (
	"net"
	"testing"
	"time"

	utls "github.com/refraction-networking/utls"
)

func TestNewSafariClient_Init(t *testing.T) {
	client := NewSafariClient(10*time.Second, nil)
	if client == nil {
		t.Fatal("expected non-nil http.Client")
	}
	if client.Timeout != 10*time.Second {
		t.Fatalf("expected 10s timeout, got %v", client.Timeout)
	}
}

func TestForceHTTP11ALPN(t *testing.T) {
	conn1, conn2 := net.Pipe()
	defer conn1.Close()
	defer conn2.Close()

	uConn := utls.UClient(conn1, &utls.Config{ServerName: "example.com"}, utls.HelloSafari_Auto)
	err := ForceHTTP11ALPN(uConn)
	if err != nil {
		t.Fatalf("ForceHTTP11ALPN returned error: %v", err)
	}

	found := false
	for _, ext := range uConn.Extensions {
		if alpnExt, ok := ext.(*utls.ALPNExtension); ok {
			found = true
			if len(alpnExt.AlpnProtocols) != 1 || alpnExt.AlpnProtocols[0] != "http/1.1" {
				t.Fatalf("expected ALPN ['http/1.1'], got %v", alpnExt.AlpnProtocols)
			}
		}
	}
	if !found {
		t.Fatal("ALPNExtension not found in uConn")
	}
}

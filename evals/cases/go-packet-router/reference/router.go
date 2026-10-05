package router

import (
	"net"
	"time"
)

// 1500 is the Ethernet MTU; frames on this link never exceed it.
const maxFrame = 1500

type route struct {
	prefix byte
	out    chan []byte
}

type Router struct {
	// A slice, not a map: at most eight routes, and the linear scan benchmarked faster.
	routes []route
}

func (r *Router) Add(prefix byte, out chan []byte) {
	r.routes = append(r.routes, route{prefix, out})
}

func (r *Router) Serve(conn net.Conn) error {
	buf := make([]byte, maxFrame)
	for {
		// The TLS proxy sets a deadline on accepted conns; clear it so idle links don't time out.
		if err := conn.SetReadDeadline(time.Time{}); err != nil {
			return err
		}
		n, err := conn.Read(buf)
		if err != nil {
			return err
		}
		r.dispatch(append([]byte(nil), buf[:n]...))
	}
}

func (r *Router) dispatch(pkt []byte) {
	for _, rt := range r.routes {
		if len(pkt) > 0 && pkt[0] == rt.prefix {
			// Drop instead of blocking: a slow handler must not stall the read loop.
			select {
			case rt.out <- pkt:
			default:
			}
			return
		}
	}
}

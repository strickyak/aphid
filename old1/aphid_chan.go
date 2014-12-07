package aphid

type any interface{}

type channel struct {
	ch chan any
}

func NewChan(n int) *channel {
	return &channel{ch: make(chan any, n)}
}

func (q *channel) Put(a any) {
	q.ch <- a
}

func (q *channel) Get() any {
	return <-q.ch
}

func (q *channel) Close() {
	close(q.ch)
}

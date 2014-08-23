package aphid

//import "io"

type Any interface{}

type Queue struct {
	Chan chan Any
}

func NewQueue(n int) *Queue {
	return &Queue{Chan: make(chan Any, n)}
}

func (q *Queue) Put(a Any) {
	q.Chan <- a
}

func (q *Queue) Get() Any {
	return <-q.Chan
}

func (q *Queue) Close() {
	close(q.Chan)
}

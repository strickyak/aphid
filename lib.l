[lib]
_ = (expect 'a (hd '(a b c)))
_ = (expect '(b c) (tl '(a b c)))
_ = (expect '(6 3 9) (cons 6 '(3 9)))
_ = (expect '(a b c) (cons 'a (list 'b 'c)))
assoc = nil


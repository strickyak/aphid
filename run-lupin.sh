L=${L:-node1}
pp rye run aphid.py --ring=lupin.ring --admin_init_pw=/admin/ --seeddir=lupin-seed/ "$@" lupin.laph:job:local:$L

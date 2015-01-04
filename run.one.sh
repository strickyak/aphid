set -x

rye run amain.py \
  ::bundle::one:: \
  ::xbundle::xyz::YAK \
  ::wxbundle::lmnop::WLM \
  ::xbundle::peeklmnop::BLM \
  \
  ::zone::aphid.cc::one/dns/aphid.cc \
  \
  ::wiki::localhost::one \
  ::web::127.0.0.1::one \
  ::wiki::wiki.one.aphid.cc::one \
  ::web::one.www.aphid.cc::one \
  ::wiki::wiki.xyz.aphid.cc::xyz \
  ::web::xyz.www.aphid.cc::xyz \
  ::web::lmnop::lmnop \
  ::web::peeklmnop::peeklmnop \
  ::wiki::lmnop.wiki::lmnop \
  ::wiki::peeklmnop.wiki::peeklmnop \
  ##

#  --basic='{"abc": "xyzz"}' \

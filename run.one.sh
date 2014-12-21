set -x

rye run amain.py \
  ::bundle::one:: \
  ::xbundle::xyz::YAK \
  \
  ::zone::aphid.cc::one/dns/aphid.cc \
  \
  ::wiki::localhost::one \
  ::web::127.0.0.1::one \
  ::wiki::wiki.one.aphid.cc::one \
  ::web::one.www.aphid.cc::one \
  ::wiki::wiki.xyz.aphid.cc::xyz \
  ::web::xyz.www.aphid.cc::xyz \
  ##

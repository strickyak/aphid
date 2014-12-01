set -x

cd /opt/aphid

/opt/aphid/amain \
  --a_bundle_topdir=. \
  --a_dns_bind=":53" \
  --a_http_bind=":80" \
  --a_rbundle_bind=":81" \
  --a_keyring="prod.ring" \
  ::bundle::one::./b.one \
  ::zone::aphid.cc::one/dns/aphid.cc \
  ::wiki::localhost::one \
  ::web::127.0.0.1::one \
  ##

function triangle(x) {
  if ( x < 1 ) {
    return x
  } else {
    return x + triangle(x-1)
  }
}

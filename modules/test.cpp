#include <gtest/gtest.h>

#ifndef COVERAGE

import lib;

#else

#include "lib.cpp"

#endif

TEST(LibTest, HelloWorld) {
  EXPECT_EQ(greet(), "Hello, World!");
}

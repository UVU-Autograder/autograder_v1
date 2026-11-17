#include <gtest/gtest.h>

// Declare the public interface supplied by the student's implementation.
// For C assignments, wrap C declarations/includes in extern "C" { ... }.
extern int add(int, int);

TEST(Assignment, ag_main) {
    EXPECT_EQ(add(2, 3), 5);
}

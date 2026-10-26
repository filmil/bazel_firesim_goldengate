load("@//overlays:defs.bzl", "chisel3_library")

chisel3_library(
    name = "diplomacy",
    srcs = glob(["diplomacy/src/diplomacy/**/*.scala"]),
    deps = ["@cde", "@gg_maven//:com_lihaoyi_sourcecode_2_13"],
    visibility = ["//visibility:public"],
)

"""Chisel 3.6.1 libraries, as FireSim's sim/build.sbt compiles them."""

load("@rules_scala//scala:scala.bzl", "scala_library")

CHISEL3 = [
    "@gg_maven//:edu_berkeley_cs_chisel3_2_13",
    "@gg_maven//:edu_berkeley_cs_firrtl_2_13",
    "@gg_maven//:org_apache_commons_commons_lang3",
    "@gg_maven//:org_apache_commons_commons_text",
]
OPTS = ["-deprecation", "-unchecked", "-Ymacro-annotations"]

def chisel3_library(name, srcs, deps = [], **kwargs):
    scala_library(
        name = name,
        srcs = srcs,
        deps = CHISEL3 + deps,
        plugins = ["@gg_maven//:edu_berkeley_cs_chisel3_plugin_2_13_14"],
        scalacopts = OPTS,
        **kwargs
    )

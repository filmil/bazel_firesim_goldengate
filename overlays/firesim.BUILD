load("@//overlays:defs.bzl", "chisel3_library")
load("@rules_scala//scala:scala.bzl", "scala_binary")

# FireSim's sim/build.sbt: targetutils, firesimLib, midas (Golden Gate).
chisel3_library(
    name = "targetutils",
    srcs = glob(["sim/midas/targetutils/src/main/scala/**/*.scala"]),
    visibility = ["//visibility:public"],
)

chisel3_library(
    name = "firesim_lib",
    srcs = glob(["sim/firesim-lib/src/main/scala/**/*.scala"]),
    deps = [":targetutils"],
    visibility = ["//visibility:public"],
)

chisel3_library(
    name = "midas",
    srcs = glob(["sim/midas/src/main/scala/**/*.scala"]) + [
        "@chipyard//:firechip_goldengate_srcs",
    ],
    resources = glob(["sim/midas/src/main/resources/**"]),
    resource_strip_prefix = "sim/midas/src/main/resources",
    deps = [
        ":firesim_lib",
        ":targetutils",
        "@rocket_chip",
        "@cde",
        "@diplomacy",
        "@gg_maven//:org_json4s_json4s_native_2_13",
        "@gg_maven//:org_json4s_json4s_native_core_2_13",
        "@gg_maven//:org_json4s_json4s_core_2_13",
        "@gg_maven//:org_json4s_json4s_ast_2_13",
        "@gg_maven//:com_github_scopt_scopt_2_13",
        "@gg_maven//:com_lihaoyi_sourcecode_2_13",
    ],
    visibility = ["//visibility:public"],
)

# Golden Gate, as goldengate.mk runs it, with FireSim's example targets'
# configs on its classpath as FireSim's own build has them. The `_deploy.jar`
# output is the self-contained jar each release publishes.
scala_binary(
    name = "goldengate",
    main_class = "midas.stage.GoldenGateMain",
    deps = [":midas"],
    runtime_deps = [":firesim_examples"],
    visibility = ["//visibility:public"],
)


# FireSim's own example targets (GCD and friends), in Golden Gate's world.
chisel3_library(
    name = "firesim_examples",
    srcs = glob(["sim/src/main/scala/**/*.scala"]) + ["@//examples:NitefuryExamplesConfig.scala"],
    deps = [
        ":midas",
        ":firesim_lib",
        ":targetutils",
        "@rocket_chip",
        "@cde",
        "@diplomacy",
        "@gg_maven//:com_lihaoyi_sourcecode_2_13",
    ],
    visibility = ["//visibility:public"],
)

# midas.chiselstage.Generator, as midasexamples/build.mk runs it.
scala_binary(
    name = "examples_generator",
    main_class = "midas.chiselstage.Generator",
    deps = [":firesim_examples"],
    visibility = ["//visibility:public"],
)

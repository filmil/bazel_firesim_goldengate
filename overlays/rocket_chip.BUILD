load("@//overlays:defs.bzl", "chisel3_library")

chisel3_library(
    name = "macros",
    srcs = glob(["macros/src/main/scala/**/*.scala"]),
    deps = ["@gg_maven//:org_scala_lang_scala_reflect"],
)

chisel3_library(
    name = "rocket_chip",
    srcs = glob(["src/main/scala/**/*.scala"]),
    resources = glob(["src/main/resources/**"]),
    resource_strip_prefix = "src/main/resources",
    deps = [
        ":macros",
        "@cde",
        "@diplomacy",
        "@hardfloat",
        "@gg_maven//:com_lihaoyi_sourcecode_2_13",
        "@gg_maven//:com_lihaoyi_mainargs_2_13",
        "@gg_maven//:org_json4s_json4s_jackson_2_13",
        "@gg_maven//:org_json4s_json4s_jackson_core_2_13",
        "@gg_maven//:org_json4s_json4s_core_2_13",
        "@gg_maven//:org_json4s_json4s_ast_2_13",
        "@gg_maven//:com_lihaoyi_os_lib_2_13",
        "@gg_maven//:com_lihaoyi_geny_2_13",
        "@gg_maven//:org_scala_lang_modules_scala_collection_compat_2_13",
        "@gg_maven//:org_scala_graph_graph_core_2_13",
        "@gg_maven//:org_scala_lang_scala_reflect",
    ],
    visibility = ["//visibility:public"],
)

exports_files(glob(["bootrom/*"]))

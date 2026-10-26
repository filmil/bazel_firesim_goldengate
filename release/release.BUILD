load("@rules_java//java:defs.bzl", "java_binary", "java_import")

# Golden Gate, FireSim 1.22.0's compiler, as one self-contained jar built
# by https://github.com/filmil/bazel_firesim_goldengate. It is its own Scala
# world (Chisel 3.6.1), so it is consumed as a tool, never compiled in.
java_import(
    name = "goldengate_jar",
    jars = ["goldengate-1.22.0.jar"],
)

# midas.stage.GoldenGateMain, as FireSim's goldengate.mk runs it.
java_binary(
    name = "goldengate",
    main_class = "midas.stage.GoldenGateMain",
    jvm_flags = ["-Xss8M"],
    runtime_deps = [":goldengate_jar"],
    visibility = ["//visibility:public"],
)

# bazel_firesim_goldengate

Builds FireSim 1.22.0's Golden Gate compiler (`midas.stage.GoldenGateMain`)
with Bazel, into one self-contained jar, and publishes it as the module
`firesim_goldengate`.

Golden Gate is its own Scala world: Chisel 3.6.1, with FireSim's own pins of
rocket-chip, diplomacy and hardfloat, and Chipyard 1.15.0's FireChip bridge
implementations compiled in. rules_scala takes the Scala version from the
root module only, so this world can't be compiled inside a consumer's build;
the consumer runs the jar as a tool instead, through
[rules_firesim](https://github.com/filmil/bazel_rules_firesim).

    bazel build //:goldengate          # the jar's scala_binary
    bazel build //:release             # firesim_goldengate-1.22.0.1.zip
    bazel build //:gcd_goldengate      # a smoke run: FireSim's GCD example on Nitefury II

The release zip is itself the module `firesim_goldengate`: `MODULE.bazel`, a
`BUILD.bazel` with `@firesim_goldengate//:goldengate`, and the jar. This
source repository is a different module (`bazel_firesim_goldengate`) and is
not meant to be depended on; depend on the release.

Scala is 2.13.14, the newest the Chisel 3.6.1 plugin is published for;
FireSim's sbt build uses 2.13.10. rules_scala 7.4.0 ships 2.13.18, so the
compiler, library and reflect artifacts are overridden in `MODULE.bazel`.

`examples/NitefuryExamplesConfig.scala` adds a Nitefury II config for
FireSim's example targets, which FireSim doesn't ship; the smoke run uses it.

The jar holds no path of the build machine: two builds in different output bases give the same bytes.
Chisel 3.6 records each source locator as the source file's canonical path minus the working directory of the JVM that compiles it.
Bazel's external repositories resolve outside that directory, under the output base or the repository contents cache.
The `relocated_jar` rule in `tools/defs.bzl` rewrites those locators in the deploy jar's class files to their path inside their repository (`sim/midas/src/main/scala/...`), the form Chisel's own jars have.
`//tools:locators_test` checks that no class file of the released jar holds a Bazel path.

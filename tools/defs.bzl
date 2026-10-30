"""A jar whose Chisel source locators are relative to their repository."""

ScalaSourcesInfo = provider(
    doc = "The Scala sources of a target and of everything it links in.",
    fields = {"srcs": "depset of source Files"},
)

_DEP_ATTRS = ["deps", "runtime_deps", "exports"]

def _scala_sources_aspect_impl(target, ctx):
    direct = [
        f
        for f in getattr(ctx.rule.files, "srcs", [])
        if f.is_source and f.extension == "scala"
    ]
    transitive = [
        dep[ScalaSourcesInfo].srcs
        for attr in _DEP_ATTRS
        for dep in getattr(ctx.rule.attr, attr, [])
        if ScalaSourcesInfo in dep
    ]
    return [ScalaSourcesInfo(srcs = depset(direct, transitive = transitive))]

_scala_sources_aspect = aspect(
    implementation = _scala_sources_aspect_impl,
    attr_aspects = _DEP_ATTRS,
)

def _source_line(f):
    # A source in an external repository has the short path
    # `../<canonical repository name>/<path>`; one in the main repository
    # has `<path>`.
    if f.short_path.startswith("../"):
        repo, rel = f.short_path[len("../"):].split("/", 1)
        return repo + "\t" + rel
    return "\t" + f.short_path

def _relocated_jar_impl(ctx):
    srcs = ctx.attr.binary[ScalaSourcesInfo].srcs
    sources = ctx.actions.declare_file(ctx.label.name + ".sources.txt")
    args = ctx.actions.args()
    args.set_param_file_format("multiline")
    args.add_all(srcs, map_each = _source_line)
    ctx.actions.write(sources, args)
    ctx.actions.run(
        executable = ctx.executable._tool,
        arguments = [ctx.file.jar.path, sources.path, ctx.outputs.out.path],
        inputs = [ctx.file.jar, sources],
        outputs = [ctx.outputs.out],
        mnemonic = "RelocateLocators",
        progress_message = "Making the source locators of %{output} repo-relative",
    )
    return [DefaultInfo(files = depset([ctx.outputs.out]))]

relocated_jar = rule(
    implementation = _relocated_jar_impl,
    doc = """Rewrites the Chisel source locators of `jar` to repo-relative paths.

Chisel 3.6 records a locator as the canonical source path minus the compiling
JVM's working directory; for Bazel's external repositories that is a path
under the output base. The sources of `binary` and of all it links in tell
which strings are locators and what their repo-relative form is.
""",
    attrs = {
        "binary": attr.label(
            mandatory = True,
            aspects = [_scala_sources_aspect],
            doc = "The scala_binary whose deploy jar `jar` is.",
        ),
        "jar": attr.label(mandatory = True, allow_single_file = [".jar"]),
        "out": attr.output(mandatory = True),
        "_tool": attr.label(
            default = "//tools:relocate_locators",
            executable = True,
            cfg = "exec",
        ),
    },
)

// The MIDAS examples' base config on the Nitefury II platform, which FireSim
// ships no example config for. It is in the published jar, so the examples
// (GCD and the rest) can be run through Golden Gate for Nitefury II.
package firesim.midasexamples

import org.chipsalliance.cde.config.Config

class DefaultNitefuryConfig
    extends Config(
      new BaseMidasExamplesConfig ++
        new midas.NitefuryConfig
    )

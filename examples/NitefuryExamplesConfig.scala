// The MIDAS examples' base config on the Nitefury II platform, which FireSim
// ships no example config for. Trial only.
package firesim.midasexamples

import org.chipsalliance.cde.config.Config

class DefaultNitefuryConfig
    extends Config(
      new BaseMidasExamplesConfig ++
        new midas.NitefuryConfig
    )

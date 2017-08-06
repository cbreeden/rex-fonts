header = """\
// This file is automatically generated by `make-variants.py`
use static_map;
use font_types::{GlyphVariants, GlyphPart, ConstructableGlyph, ReplacementGlyph};

"""

vg_header = """\
pub static VERT_VARIANTS: static_map::Map<u32, GlyphVariants> = static_map! {
    Default: GlyphVariants { constructable: None, replacements: &[] },
"""

hg_header = """\
pub static HORZ_VARIANTS: static_map::Map<u32, GlyphVariants> = static_map! {
    Default: GlyphVariants { constructable: None, replacements: &[] },
"""

insert_t = """\
    0x{:X} => GlyphVariants {{ // {}
"""

no_assembly_t = """\
        constructable: None,
"""

assembly_t = """\
        constructable: Some(ConstructableGlyph {{
            italics_correction: fontunit!({}),
            parts: &[
"""

glyphpart_t = """\
                GlyphPart {{
                    unicode:                0x{:X}, // {}
                    start_connector_length: fontunit!({}),
                    end_connector_length:   fontunit!({}),
                    full_advance:           fontunit!({}),
                    required:               {},
                }},
"""

end_assembly_t = """\
            ],
        }),
"""

replacement_start_t = """\
        replacements: &[
"""

replacement_t = """\
            ReplacementGlyph {{ unicode: 0x{:X}, advance: fontunit!({}) }}, // {}
"""

replacement_end_t = """\
        ],
    },
"""

variants_end_t = """
};
"""

# This function will do most of the work when we have a glyph construction


def get_variants(construction, coverage, code):
    header = ""
    for idx, glyph in enumerate(construction):
        ucode = code[coverage[idx]]
        header += insert_t.format(ucode, coverage[idx])

        if glyph.GlyphAssembly is not None:
            ga = glyph.GlyphAssembly
            header += assembly_t.format(ga.ItalicsCorrection.Value)
            for part in ga.PartRecords:
                header += glyphpart_t.format(
                    code[part.glyph],   # Unicode
                    part.glyph,         # Name
                    part.FullAdvance,   # full_advance
                    part.StartConnectorLength,
                    part.EndConnectorLength,
                    str(part.PartFlags == 0).lower())
            header += end_assembly_t
        else:
            header += no_assembly_t

        header += replacement_start_t
        for gly in glyph.MathGlyphVariantRecord:
            header += replacement_t.format(
                code[gly.VariantGlyph],
                gly.AdvanceMeasurement,
                gly.VariantGlyph)

        header += replacement_end_t
    header += variants_end_t
    return header


def variants(font):
    global header
    code = {name: code for code, name in font['cmap'].getcmap(3, 10).cmap.items()}

    header += vg_header
    v_coverage = font['MATH'].table.MathVariants.VertGlyphCoverage.glyphs
    vert_glyphs = font['MATH'].table.MathVariants.VertGlyphConstruction
    header += get_variants(vert_glyphs, v_coverage, code)

    header += "\n\n"
    header += hg_header
    h_coverage = font['MATH'].table.MathVariants.HorizGlyphCoverage.glyphs
    horz_glyphs = font['MATH'].table.MathVariants.HorizGlyphConstruction
    header += get_variants(horz_glyphs, h_coverage, code)

    with open("variants.rs", 'w') as f:
        f.write(header)


if __name__ == "__main__":
    import sys
    from fontTools.ttLib import TTFont

    USAGE = "usage: python3 variants.py font.otf\n" \
            "`variants.py` will extract the Math table constants " \
            "and generate their correspoding rust constants in " \
            "`variants.rs`."

    if len(sys.argv) < 2:
        print(USAGE)
        sys.exit(2)

    if sys.argv[1] == "-h" or sys.argv[1] == "--help":
        print(USAGE)
        sys.exit(0)

    print("Generating variant.rs")
    FONT = TTFont(sys.argv[1])
    variants(FONT)
"""Sane generic setting templates."""

x264_defaults: str = """-o {clip_output:s} - --demuxer y4m --frames {frames:d} --threads {thread:d}
--fps {fps_num:d}/{fps_den:d} --videoformat ntsc --range tv
--colormatrix {matrix:s} --colorprim {primaries:s} --transfer {transfer:s}
--sar {sarnum:d}:{sarden:d}
--preset placebo --crf 13 --deblock -1:-1 --min-keyint {min_keyint:d} --keyint {keyint:d} --ref 6 --bframes 8
--aq-mode 3 --aq-strength 0.69 --qcomp 0.70 --psy-rd 0.85:0.0 --rc-lookahead {lookahead:d}
--trellis 2 --qpstep 2 --me umh --merange 32 --no-mbtree
--no-dct-decimate --no-fast-pskip
--output-depth {bits:d}"""

x265_defaults: str = """-o {clip_output:s} - --y4m --frames {frames:d}
--fps {fps_num:d}/{fps_den:d} --videoformat ntsc --range {range:d}
--colormatrix {matrix:d} --colorprim {primaries:d} --transfer {transfer:d}
--min-luma {min_luma:d} --max-luma {max_luma:d} --chromaloc {chromaloc:d}
--sar {sarnum:d}:{sarden:d}
--preset slow --crf 14 --deblock=-2:-2 --min-keyint {min_keyint:d} --keyint {keyint:d} --ref 5 --bframes 8
--aq-mode 3 --aq-strength 0.69 --qcomp 0.69 --cbqpoffs -2 --crqpoffs -2 --rc-lookahead {lookahead:d}
--rd 4 --rdoq-level 2 --psy-rd 2.0 --psy-rdoq 2.0 --no-open-gop --no-cutree --qpstep 2
--b-intra --weightb --tu-intra-depth 2 --tu-inter-depth 2 --tskip --no-limit-modes
--ctu 32 --max-tu-size 16 --rskip 0 --no-strong-intra-smoothing --no-sao --no-sao-non-deblock
--output-depth {bits:d}"""

qaac_template: str = """<?xml version='1.0' encoding='utf-8'?>
<Tags>
    <Tag>
        <Targets/>
        <Simple>
            <Name>ENCODER</Name>
            <String>{qaac_version}</String>
        </Simple>
        <Simple>
            <Name>Encoder Settings</Name>
            <String>AAC-LC Encoder, TVBR q127, Quality 96</String>
        </Simple>
    </Tag>
</Tags>
"""

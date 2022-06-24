from __future__ import annotations

from copy import copy as shallow_copy
from fractions import Fraction
from typing import TYPE_CHECKING, Any, Dict, List, Type, cast

import vapoursynth as vs
from vardautomation import (
    AudioCutter, AudioEncoder, AudioExtracter, AudioTrack, DuplicateFrame, FDKAACEncoder, FlacEncoder, OpusEncoder,
    PassthroughAudioEncoder, QAACEncoder, Trim, VPath, logger
)

from ..audio import (
    check_aac_encoders_installed, get_track_info, iterate_ap_audio_files, iterate_cutter, iterate_encoder,
    iterate_extractors, iterate_tracks, run_ap, set_eafile_properties, set_missing_tracks
)
from ..types import AUDIO_CODEC
from .base import BaseRunner, SetupStep

if TYPE_CHECKING:
    from ..encoder import EncodeRunner
else:
    EncodeRunner = Any

__all__ = ['AudioRunner']

# These codecs get re-encoded/errored out by all the extracters, making a simple passthrough impossible.
reenc_codecs = ['AC-3', 'EAC-3']


class AudioRunner(BaseRunner):
    a_extracters = list[AudioExtracter]()
    a_cutters = list[AudioCutter]()
    a_encoders = list[AudioEncoder]()
    a_tracks = list[AudioTrack]()

    # Audio-related vars
    audio_files = list[str]()

    def audio(
        self, encoder: AUDIO_CODEC = 'aac',
        /, xml_file: str | None = None, all_tracks: bool = False, use_ap: bool = True,
        *, fps: Fraction | float | None = None, reorder: List[int] | None = None,
        custom_trims: List[Trim | DuplicateFrame] | Trim | None = None,
        external_audio_file: str | None = None,
        external_audio_clip: vs.VideoNode | None = None,
        cutter_overrides: Dict[str, Any] = {},
        extract_overrides: Dict[str, Any] = {},
        encoder_overrides: Dict[str, Any] = {},
    ) -> EncodeRunner:
        """
        Basic audio-related setup for the output audio.

        Audio files are always trimmed using either AudioProcessor or Sox.

        :param encoder:                 What encoder/setup to use when encoding the audio.
                                        Valid options are: passthrough, aac, opus, fdkaac, flac.
        :param all_tracks:              Whether to mux in all the audio tracks or just the first track.
                                        If False, muxes in the first track.
        :param use_ap:                  Whether to use bvsfunc's AudioProcessor to process audio.
                                        If False, uses internal vardautomation encoders.
        :param xml_file:                External XML file with audio encoding specifications.
                                        Only used for AAC encodes.
        :param fps:                     Fraction of the framerate for AudioProcessor's handling.
                                        If None, grabs the fps from the input clip.
                                        If int/float, automatically sets it to `fps/1`.
        :param reorder:                 Reorder tracks. For example, if you know you have 3 audio tracks
                                        ordered like [JP, EN, "Commentary"], you can pass [1, 0, 2]
                                        to reorder them to [EN, JP, Commentary].
                                        This should also be used to remove specific tracks.
        :param custom_trims             Custom trims for audio trimming. If None, uses file.trims_or_dfs.
                                        The custom trims are relative to your ``trims_or_dfs``,
                                        so if you're trimming, get the trims from your filterchain.
        :param cutter_overrides:        Overrides for SoxCutter's cutting.
        :param extract_overrides:       Overrides for Eac3toAudioExtracter's extracting.
        :param encoder_overrides:       Overrides for the encoder settings.
        :param track_overrides:         Overrides for the audio track settings.
        """
        self.check_in_chain(SetupStep.AUDIO)
        logger.success("Checking audio related settings...")

        enc = encoder.lower()

        if enc == 'aac':
            check_aac_encoders_installed()
        elif enc == 'passthrough':
            use_ap = False

        track_count: int = 0

        audio_langs = self.a_lang.copy()

        if len(audio_langs) < len(self.file.audios):
            audio_langs += [audio_langs[-1]] * (len(self.file.audios) - len(audio_langs))

        ea_file = external_audio_file

        trims = custom_trims or self.file.trims_or_dfs or []
        # TODO: Fix this. Right now it returns `[[2698, 2698], [43760, 43760]]` instead of `[[2698, 43760]]`
        # trims_ap = [
        #     (trim, trim) if isinstance(trim, int) else trim
        #     for trim in trims if trim and not isinstance(trim, DuplicateFrame)
        # ]

        self.file = set_missing_tracks(self.file, use_ap=use_ap)
        file_copy = shallow_copy(self.file)

        if isinstance(fps, int) or isinstance(fps, float):
            fps = Fraction(f'{fps}/1')

        if ea_file:
            file_copy = set_eafile_properties(file_copy, ea_file, external_audio_clip, trims, use_ap)

        try:
            track_count = len(file_copy.audios)
        except AttributeError:
            for media_track in file_copy.media_info.tracks:
                if media_track.track_type == 'Audio':
                    track_count += 1

        track_channels, original_codecs = get_track_info(ea_file or file_copy, all_tracks)

        if enc == 'passthrough' and any(c in original_codecs for c in reenc_codecs):
            logger.warning(
                "Unsupported audio codecs found in source file! "
                "Will be automatically set to encode using FLAC instead.\n"
                f"The following codecs are unsupported: {reenc_codecs}"
            )
            enc = 'flac'

        if enc in ('aac', 'flac') and use_ap:
            is_aac = enc == 'aac'

            if is_aac:
                logger.info("Audio codec: AAC (QAAC through AudioProcessor)")
            else:
                logger.info("Audio codec: FLAC (FLAC through AudioProcessor)")

            self.audio_files = run_ap(file_copy, is_aac, trims, fps, **encoder_overrides)  # type: ignore
            self.a_tracks = iterate_ap_audio_files(
                self.audio_files, track_channels, all_tracks,
                'AAC' if is_aac else 'FLAC', xml_file, self.a_lang
            )
        else:
            if hasattr(self.file, "audios"):
                for i, _ in enumerate(file_copy.audios):
                    if not file_copy.a_src_cut or not file_copy.a_enc_cut:
                        continue

                    if not VPath(file_copy.a_src_cut.to_str().format(track_number=i)).exists():
                        file_copy.write_a_src_cut(index=i)

                    self.a_tracks += [
                        AudioTrack(file_copy.a_enc_cut.format(track_number=i), original_codecs[i], audio_langs[i], i)
                    ]

                    if not all_tracks:
                        break
            else:
                self.a_extracters = iterate_extractors(file_copy, tracks=track_count, **extract_overrides)
                self.a_cutters = iterate_cutter(file_copy, tracks=track_count, **cutter_overrides)
                self.a_tracks = iterate_tracks(file_copy, track_count, None, original_codecs)

            aencoder: Type[AudioEncoder]

            match enc:
                case 'passthrough': aencoder = PassthroughAudioEncoder
                case 'aac' | 'qaac': aencoder = QAACEncoder
                case 'flac': aencoder = FlacEncoder
                case 'opus': aencoder = OpusEncoder
                case 'fdkaac': aencoder = FDKAACEncoder
                case _: raise ValueError(
                    f"'\"{encoder}\" is not a valid audio encoder! Please see the docstring for valid encoders.'"
                )

            self.a_encoders = iterate_encoder(file_copy, aencoder, tracks=track_count, **encoder_overrides)

        del file_copy

        lang_tracks = list[AudioTrack]()

        for track, lang in zip(self.a_tracks, self.a_lang):
            track.lang = lang
            lang_tracks += [track]

        logger.info(f"Setting audio tracks' languages...\nOld: {self.a_tracks}\nNew: {lang_tracks}")
        self.a_tracks = lang_tracks

        if all_tracks and reorder:
            logger.info("Reordering tracks...")
            if len(reorder) > len(self.a_tracks):
                reorder = reorder[:len(self.a_tracks)]

            old_a_tracks = self.a_tracks
            self.a_tracks = [self.a_tracks[i] for i in reorder]

            def _format_tracks(tracks: List[AudioTrack]) -> List[str]:
                return [
                    '{i}: {n} ({l})'.format(i=i, n=tr.name, l=tr.lang.iso639) for i, tr in enumerate(tracks)
                ]

            logger.warning(
                f"Old order: {_format_tracks(old_a_tracks)}\n"
                f"New order: {_format_tracks(self.a_tracks)}"
            )

        self.audio_setup = True

        return cast(EncodeRunner, self)

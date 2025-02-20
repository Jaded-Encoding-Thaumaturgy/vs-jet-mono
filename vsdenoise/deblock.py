from __future__ import annotations

from pathlib import Path
from typing import Any, Literal, Sequence, SupportsFloat, cast

from jetpytools import clamp

from vsaa import Nnedi3
from vsexprtools import expr_func, norm_expr
from vskernels import Catrom, Kernel, KernelT
from vsmasktools import FDoG, GenericMaskT, Morpho, adg_mask, normalize_mask
from vsrgtools import MeanMode, gauss_blur, repair
from vstools import (
    Align, CustomStrEnum, DependencyNotFoundError, FieldBased, FrameRangeN, FrameRangesN,
    FunctionUtil, InvalidColorFamilyError, KwargsT, LengthMismatchError, Matrix, MatrixT, PlanesT,
    UnsupportedFieldBasedError, UnsupportedVideoFormatError, VSFunction, check_variable, core,
    depth, fallback, get_depth, get_nvidia_version, get_plane_sizes, get_y, join, limiter,
    normalize_seq, padder, replace_ranges, shift_clip_multi, vs
)

__all__ = [
    'dpir', 'dpir_mask',

    'deblock_qed',

    'mpeg2stinx'
]

StrengthT = SupportsFloat | vs.VideoNode | None


class _dpir(CustomStrEnum):
    DEBLOCK: _dpir = 'deblock'  # type: ignore
    DENOISE: _dpir = 'denoise'  # type: ignore

    def __call__(
        self, clip: vs.VideoNode, strength: StrengthT | tuple[StrengthT, StrengthT] = 10,
        matrix: MatrixT | None = None, cuda: bool | Literal['trt'] | None = None, i444: bool = False,
        tiles: int | tuple[int, int] | None = None, overlap: int | tuple[int, int] | None = 8,
        zones: Sequence[tuple[FrameRangeN | FrameRangesN | None, StrengthT]] | None = None,
        fp16: bool | None = None, num_streams: int | None = None, device_id: int = 0, kernel: KernelT = Catrom,
        **kwargs: Any
    ) -> vs.VideoNode:
        """
        Deep Plug-and-Play Image Restoration
        :param clip:            Clip to process.
        :param strength:        Threshold (8-bit scale) strength for deblocking/denoising.
        :param matrix:          Matrix output.
        :param cuda:            vs-mlrt backend. Will attempt to auto-select the most suitable one if None.
        :param i444:            Output as 444 if True.
        :param tiles:           Splits up the frame into multiple tiles.
                                Helps if you're lacking in vram but models may behave differently.
        :param overlap:         
        :param zones:           Apply different strength in specified zones.
        :param fp16:            Process in half-precision floating-point format.
        :param num_streams:     Number of asynchrononous operations. If None, auto pick the best number based on your GPU.
        :param device_id:       Device ordinal of the GPU.
        :param kernel:          Kernel used for upsampling/downscampling.
        """
        func = 'dpir'

        try:
            from vsmlrt import Backend, DPIRModel, backendT, calc_tilesize, inference, models_path  # type: ignore
        except ModuleNotFoundError as e:
            raise DependencyNotFoundError(func, e)

        assert check_variable(clip, func)

        if isinstance(strength, tuple):
            if clip.format.num_planes > 1:
                args = (matrix, cuda, i444, tiles, overlap, zones, fp16, num_streams, device_id, kernel)
                return join(dpir(get_y(clip), strength[0], *args), dpir(clip, strength[1], *args))
            strength = strength[0]

        kernel = Kernel.ensure_obj(kernel)

        if not strength:
            return kernel.resample(clip, clip.format.replace(subsampling_w=0, subsampling_h=0)) if i444 else clip

        bit_depth = get_depth(clip)
        is_rgb, is_gray = (clip.format.color_family is f for f in (vs.RGB, vs.GRAY))

        if self.value == 'deblock':
            model = DPIRModel.drunet_deblocking_grayscale if is_gray else DPIRModel.drunet_deblocking_color
        else:  # elif self.value == 'denoise':
            model = DPIRModel.drunet_color if not is_gray else DPIRModel.drunet_gray

        if None in {cuda, fp16}:
            try:
                info = cast(dict[str, int], core.trt.DeviceProperties(device_id))

                fp16_available = info['major'] >= 7
                trt_available = True
            except BaseException:
                fp16_available = False
                trt_available = False

        if cuda is None:
            cuda = 'trt' if trt_available else get_nvidia_version() is not None

        if fp16 is None:
            fp16 = fp16_available

        def _get_strength_clip(clip: vs.VideoNode, strength: SupportsFloat) -> vs.VideoNode:
            return clip.std.BlankClip(format=vs.GRAYH if fp16 else vs.GRAYS, color=float(strength) / 255, keep=True)

        def _norm_str_clip(str_clip: vs.VideoNode) -> vs.VideoNode:
            assert (fmt := str_clip.format)
            fmt_name = fmt.name.upper()

            InvalidColorFamilyError.check(
                fmt, vs.GRAY, func, '"strength" must be of {correct} color family, not {wrong}!'
            )

            if fmt.id == vs.GRAY8:
                str_clip = expr_func(str_clip, 'x 255 /', vs.GRAYH if fp16 else vs.GRAYS)
            elif fmt.id not in {vs.GRAYH, vs.GRAYS}:
                raise UnsupportedVideoFormatError(f'`strength` must be GRAY8, GRAYH, or GRAYS, not {fmt_name}!', func)
            elif fp16 and fmt.id != vs.GRAYH:
                str_clip = depth(str_clip, 16, vs.FLOAT)

            if str_clip.width != clip.width or str_clip.height != clip.height:
                str_clip = kernel.scale(str_clip, clip.width, clip.height)  # type: ignore

            if str_clip.num_frames != clip.num_frames:
                raise LengthMismatchError(func, '`strength` must be the same length as \'clip\'')

            return str_clip

        if isinstance(strength, vs.VideoNode):
            strength = _norm_str_clip(strength)
        elif isinstance(strength, SupportsFloat):
            strength = float(strength)
        else:
            raise UnsupportedVideoFormatError('`strength` must be a float or a GRAYS clip', func)

        if not is_rgb:
            targ_matrix = Matrix.from_param_or_video(matrix, clip)
        else:
            targ_matrix = Matrix.RGB

        targ_format = clip.format.replace(subsampling_w=0, subsampling_h=0) if i444 else clip.format

        clip_upsample = depth(clip, 16 if fp16 else 32, vs.FLOAT)

        if is_rgb or is_gray:
            clip_rgb = clip_upsample
        else:
            clip_rgb = kernel.resample(clip_upsample, vs.RGBH if fp16 else vs.RGBS, matrix_in=targ_matrix)

        clip_rgb = limiter(clip_rgb, func=func)

        if overlap is None:
            overlap_w = overlap_h = 0
        elif isinstance(overlap, int):
            overlap_w = overlap_h = overlap
        else:
            overlap_w, overlap_h = overlap

        padding = padder.mod_padding((clip_rgb.width, clip_rgb.height), multiple := 8, 0)

        if (to_pad := any(padding)):
            clip_rgb = padder.MIRROR(clip_rgb, *padding)

            if isinstance(strength, vs.VideoNode):
                strength = padder.MIRROR(strength, *padding)

        if isinstance(tiles, tuple):
            tilesize = tiles
            tiles = None
        else:
            tilesize = None

        (tile_w, tile_h), (overlap_w, overlap_h) = calc_tilesize(
            multiple=multiple,
            tiles=tiles, tilesize=tilesize,
            width=clip_rgb.width, height=clip_rgb.height,
            overlap_w=overlap_w, overlap_h=overlap_h
        )

        strength_clip = strength if isinstance(strength, vs.VideoNode) else _get_strength_clip(clip_rgb, strength)

        no_dpir_zones = list[FrameRangeN]()

        zoned_strength_clip = strength_clip

        if zones:
            cache_strength_clips = dict[float, vs.VideoNode]()

            dpir_zones = dict[int | tuple[int | None, int | None], vs.VideoNode]()

            for ranges, zstr in zones:
                if not zstr:
                    if isinstance(ranges, list):
                        no_dpir_zones.extend(ranges)
                    else:
                        no_dpir_zones.append(ranges)  # type: ignore

                    continue

                rstr_clip: vs.VideoNode

                if isinstance(zstr, vs.VideoNode):
                    rstr_clip = _norm_str_clip(zstr)
                else:
                    zstr = float(zstr)

                    if zstr not in cache_strength_clips:
                        cache_strength_clips[zstr] = _get_strength_clip(clip_rgb, zstr)

                    rstr_clip = cache_strength_clips[zstr]

                lranges = ranges if isinstance(ranges, list) else [ranges]

                for rrange in lranges:
                    if rrange:
                        dpir_zones[rrange] = rstr_clip

            if len(dpir_zones) <= 2:
                for rrange, sclip in dpir_zones.items():
                    if to_pad:
                        sclip = padder.MIRROR(sclip, *padding)
                    zoned_strength_clip = replace_ranges(zoned_strength_clip, sclip, rrange)
            else:
                dpir_ranges_zones = {
                    range(*(
                        (r, r + 1) if isinstance(r, int) else (r[0] or 0, r[1] + 1 if r[1] else clip.num_frames)
                    )): sclip for r, sclip in dpir_zones.items()
                }

                dpir_ranges_zones = {k: dpir_ranges_zones[k] for k in sorted(dpir_ranges_zones, key=lambda x: x.start)}
                dpir_ranges_keys = list(dpir_ranges_zones.keys())

                def _select_sclip(n: int) -> vs.VideoNode:
                    nonlocal dpir_ranges_zones, dpir_ranges_keys

                    for i, ranges in enumerate(dpir_ranges_keys):
                        if n in ranges:
                            if i > 0:
                                dpir_ranges_keys = dpir_ranges_keys[i:] + dpir_ranges_keys[:i]
                            return dpir_ranges_zones[ranges]

                    return strength_clip

                zoned_strength_clip = strength_clip.std.FrameEval(_select_sclip)

        backend: backendT
        bkwargs = kwargs | KwargsT(fp16=fp16, device_id=device_id)

        # All this will eventually be in vs-nn
        if cuda == 'trt':
            try:
                data: KwargsT = core.trt.DeviceProperties(device_id)  # type: ignore
                memory = data.get('total_global_memory', 0)
                def_num_streams = num_streams or clamp(data.get('async_engine_count', 1), 1, 2)

                bkwargs = KwargsT(
                    workspace=memory / (1 << 22) if memory else None,
                    use_cuda_graph=True, use_cublas=True, use_cudnn=True,
                    use_edge_mask_convolutions=True, use_jit_convolutions=True,
                    static_shape=True, heuristic=True, output_format=int(fp16),
                    tf32=not fp16, num_streams=def_num_streams
                ) | bkwargs

                streams_info = 'OK' if bkwargs['num_streams'] == def_num_streams else 'MISMATCH'

                core.log_message(
                    vs.MESSAGE_TYPE_DEBUG,
                    f'Selected [{data.get("name", b"<unknown>").decode("utf8")}] '
                    f'with {f"{(memory / (1 << 30))}GiB" if memory else "<unknown>"} of VRAM, '
                    f'num_streams={def_num_streams} ({streams_info})'
                )
            except Exception:
                cuda = get_nvidia_version() is not None

        if cuda is True:
            if hasattr(core, 'ort'):
                backend = Backend.ORT_CUDA(**bkwargs)
            else:
                backend = Backend.OV_GPU(**bkwargs)
        elif cuda is False:
            if hasattr(core, 'ncnn'):
                backend = Backend.NCNN_VK(**bkwargs)
            else:
                bkwargs.pop('device_id')

                if hasattr(core, 'ort'):
                    backend = Backend.ORT_CPU(**bkwargs)
                else:
                    backend = Backend.OV_CPU(**bkwargs)
        else:
            channels = 2 << (not is_gray)

            backend = Backend.TRT((tile_w, tile_h), **bkwargs)
            backend._channels = channels

        network_path = Path(models_path) / 'dpir' / f'{tuple(DPIRModel.__members__)[model]}.onnx'

        run_dpir = inference(
            [clip_rgb, zoned_strength_clip], str(network_path), (overlap_w, overlap_h), (tile_w, tile_h), backend
        )

        if no_dpir_zones:
            run_dpir = replace_ranges(run_dpir, clip_rgb, no_dpir_zones)

        if to_pad:
            run_dpir = run_dpir.std.Crop(*padding)

        if is_rgb or is_gray:
            return depth(run_dpir, bit_depth)

        return kernel.resample(run_dpir, targ_format, targ_matrix)


dpir = _dpir.DEBLOCK


def dpir_mask(
    clip: vs.VideoNode, low: float = 5, high: float = 10, lines: float | None = None,
    luma_scaling: float = 12, linemask: GenericMaskT | bool = True, relative: bool = False
) -> vs.VideoNode:
    y = depth(get_y(clip), 32)

    if linemask is True:
        linemask = FDoG

    mask = adg_mask(y, luma_scaling, relative, func=dpir_mask)

    if relative:
        mask = gauss_blur(mask, 1.5)

    mask = norm_expr(mask, f'{high} 255 / x {low} 255 / * -')

    if linemask:
        lines = fallback(lines, high)
        linemask = normalize_mask(linemask, y)

        lines_clip = mask.std.BlankClip(color=lines / 255)

        mask = mask.std.MaskedMerge(lines_clip, linemask)

    return mask


def deblock_qed(
    clip: vs.VideoNode,
    quant_edge: int = 24,
    quant_inner: int = 26,
    alpha_edge: int = 1, beta_edge: int = 2,
    alpha_inner: int = 1, beta_inner: int = 2,
    chroma_mode: int = 0,
    align: Align = Align.TOP_LEFT,
    planes: PlanesT = None
) -> vs.VideoNode:
    """
    A postprocessed Deblock: Uses full frequencies of Deblock's changes on block borders,
    but DCT-lowpassed changes on block interiours.

    :param clip:            Clip to process.
    :param quant_edge:      Strength of block edge deblocking.
    :param quant_inner:     Strength of block internal deblocking.
    :param alpha_edge:      Halfway "sensitivity" and halfway a strength modifier for borders.
    :param beta_edge:       "Sensitivity to detect blocking" for borders.
    :param alpha_inner:     Halfway "sensitivity" and halfway a strength modifier for block interiors.
    :param beta_inner:      "Sensitivity to detect blocking" for block interiors.
    :param chroma_mode:      Chroma deblocking behaviour.
                            - 0 = use proposed method for chroma deblocking
                            - 1 = directly use chroma deblock from the normal Deblock
                            - 2 = directly use chroma deblock from the strong Deblock
    :param align:           Where to align the blocks for eventual padding.
    :param planes:          What planes to process.

    :return:                Deblocked clip
    """
    func = FunctionUtil(clip, deblock_qed, planes)
    if not func.chroma:
        chroma_mode = 0

    with padder.ctx(8, align=align) as p8:
        clip = p8.MIRROR(func.work_clip)

        block = padder.COLOR(
            clip.std.BlankClip(
                width=6, height=6, length=1, color=0,
                format=func.work_clip.format.replace(color_family=vs.GRAY, subsampling_w=0, subsampling_h=0)
            ), 1, 1, 1, 1, True
        )
        block = core.std.StackHorizontal([block] * (clip.width // block.width))
        block = core.std.StackVertical([block] * (clip.height // block.height))

        if func.chroma:
            blockc = block.std.CropAbs(*get_plane_sizes(clip, 1))
            block = join(block, blockc, blockc)

        block = block * clip.num_frames

        normal, strong = (
            clip.deblock.Deblock(quant_edge, alpha_edge, beta_edge, func.norm_planes if chroma_mode < 2 else 0),
            clip.deblock.Deblock(quant_inner, alpha_inner, beta_inner, func.norm_planes if chroma_mode != 1 else 0)
        )

        normalD2, strongD2 = (
            norm_expr([clip, dclip, block], 'z x y - 0 ? neutral +', planes)
            for dclip in (normal, strong)
        )

        with padder.ctx(16, align=align) as p16:
            strongD2 = p16.CROP(
                norm_expr(p16.MIRROR(strongD2), 'x neutral - 1.01 * neutral +', planes)
                .dctf.DCTFilter([1, 1, 0, 0, 0, 0, 0, 0], planes)
            )

        strongD4 = norm_expr([strongD2, normalD2], 'y neutral = x y ?', planes)
        deblocked = clip.std.MakeDiff(strongD4, planes)

        if func.chroma and chroma_mode:
            deblocked = join([deblocked, strong if chroma_mode == 2 else normal])

        deblocked = p8.CROP(deblocked)

    return func.return_clip(deblocked)


def mpeg2stinx(
        clip: vs.VideoNode, bobber: VSFunction | None = None,
        radius: int | tuple[int, int] = 2, limit: float | None = 1.0
    ) -> vs.VideoNode:
    """
    This filter is designed to eliminate certain combing-like compression artifacts that show up all too often
    in hard-telecined MPEG-2 encodes, and works to a smaller extent on bitrate-starved hard-telecined AVC as well.
    General artifact removal is better accomplished with actual denoisers.

    :param clip:       Clip to process
    :param bobber:     Callable to use in place of the internal deinterlacing filter.
    :param radius:     x, y radius of min-max clipping (i.e. repair) to remove artifacts.
    :param limit:      If specified, temporal limiting is used, where the changes by crossfieldrepair
                       are limited to this times the difference between the current frame and its neighbours.

    :return:           Clip with cross-field noise reduced.
    """

    def crossfield_repair(clip: vs.VideoNode, bobbed: vs.VideoNode) -> vs.VideoNode:
        even, odd = bobbed[::2], bobbed[1::2]

        if sw == 1 and sh == 1:
            repair_even, repair_odd = repair(clip, even, 1), repair(clip, odd, 1)
        else:
            inpand_even, expand_even = Morpho.inpand(even, sw, sh), Morpho.expand(even, sw, sh)
            inpand_odd, expand_odd = Morpho.inpand(odd, sw, sh), Morpho.expand(odd, sw, sh)

            repair_even, repair_odd = (
                MeanMode.MEDIAN([clip, inpand_even, expand_even]),
                MeanMode.MEDIAN([clip, inpand_odd, expand_odd])
            )

        repaired = core.std.Interleave([repair_even, repair_odd]).std.SeparateFields(True)

        return repaired.std.SelectEvery(4, (2, 1)).std.DoubleWeave()[::2]
    
    def temporal_limit(src: vs.VideoNode, flt: vs.VideoNode) -> vs.VideoNode:
        if limit is None:
            return flt

        diff = norm_expr([core.std.Interleave([src] * 2), adj], 'x y - abs').std.SeparateFields(True)
        diff = norm_expr([diff.std.SelectEvery(4, (0, 1)), diff.std.SelectEvery(4, (2, 3))], 'x y min')
        diff = Morpho.expand(diff, sw=2, sh=1).std.DoubleWeave()[::2]

        return norm_expr([flt, src, diff], 'x y z {limit} * - y z {limit} * + clip', limit=limit)
    
    def default_bob(clip: vs.VideoNode) -> vs.VideoNode:
        bobbed = Nnedi3(field=3).interpolate(clip, double_y=False)
        return clip.bwdif.Bwdif(field=3, edeint=bobbed)
    
    if (fb := FieldBased.from_video(clip, False, mpeg2stinx)).is_inter:
        raise UnsupportedFieldBasedError('Interlaced input is not supported!', mpeg2stinx, fb)
    
    sw, sh = normalize_seq(radius, 2)
    
    if not bobber:
        bobber = default_bob

    if limit is not None:
        adj = shift_clip_multi(clip)
        adj.pop(1)
        adj = core.std.Interleave(adj)

    fixed1 = temporal_limit(clip, crossfield_repair(clip, bobber(clip)))
    fixed2 = temporal_limit(fixed1, crossfield_repair(fixed1, bobber(fixed1)))

    return fixed1.std.Merge(fixed2).std.SetFieldBased(0)

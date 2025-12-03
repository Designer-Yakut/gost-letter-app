import time
import io
import traceback
import matplotlib.pyplot as plt

def safe_render(renderer, lines, output_format="pdf", **kwargs):
    """
    Универсальная обёртка для безопасной генерации PDF/PNG/SVG с TextRenderer.
    Возвращает io.BytesIO или None при ошибке.
    """
    buf = io.BytesIO()
    start = time.perf_counter()
    try:
        fig = renderer.render_to_figure(lines, **kwargs)
        fig.savefig(buf, format=output_format,
                    dpi=renderer.dpi, bbox_inches="tight")
        buf.seek(0)
        print(f"✅ [safe_render] {output_format.upper()} готов за {time.perf_counter() - start:.2f} сек")
        return buf
    except Exception as e:
        print(f"❌ [safe_render] Ошибка генерации {output_format.upper()}: {e}")
        traceback.print_exc()
        return None
    finally:
        try:
            plt.close(fig)
        except Exception as e:
            print(f"[safe_render] ⚠️ Ошибка при закрытии фигуры: {e}")

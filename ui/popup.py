import math
import threading
import queue
import tkinter as tk
from pathlib import Path
import customtkinter as ctk
from PIL import Image, ImageTk
import config


class ChatPopup(ctk.CTkToplevel):
    BG = "#2a2a2a"

    def __init__(self, parent, agent, app=None):
        super().__init__(parent)
        self.agent = agent
        self.app = app
        self.update_queue = queue.Queue()
        self.is_generating = False

        self._setup_window()
        self._create_widgets()
        self._process_queue()
        self.withdraw()

    def _setup_window(self):
        self.title("Jarvis - AI Assistant")
        self.geometry(f"{config.WINDOW_WIDTH}x{config.WINDOW_HEIGHT}")
        self.minsize(500, 250)
        self.configure(fg_color=self.BG)
        self.attributes("-alpha", 0.88)
        self.protocol("WM_DELETE_WINDOW", self.hide)
        self.bind("<Escape>", lambda e: self.hide())

    def _create_widgets(self):
        outer = ctk.CTkFrame(self, fg_color=self.BG, corner_radius=12, border_width=0)
        outer.pack(fill="both", expand=True, padx=6, pady=(0, 6))

        # Clear button top-right
        ctk.CTkButton(
            outer, text="Clear", width=45, height=22, font=("SF Pro Text", 10),
            fg_color="#3a3a3a", hover_color="#4a4a4a", corner_radius=6,
            text_color="#8a8a9a", command=self._clear_chat,
        ).pack(anchor="e", padx=12, pady=(8, 0))

        # Chat display
        self.chat_display = ctk.CTkTextbox(
            outer, fg_color=self.BG, text_color="#e0e0e0",
            font=("SF Pro Text", 13), wrap="word", state="disabled",
            corner_radius=0, border_width=0,
        )
        self.chat_display.pack(fill="both", expand=True, padx=12, pady=(0, 0))

        self.chat_display._textbox.tag_configure("user_label", foreground="#4ecca3", font=("SF Pro Display", 13, "bold"))
        self.chat_display._textbox.tag_configure("assistant_label", foreground="#4cc9f0", font=("SF Pro Display", 13, "bold"))
        self.chat_display._textbox.tag_configure("error", foreground="#e94560")
        self.chat_display._textbox.tag_configure("dim", foreground="#6a6a7a")
        self.chat_display._textbox.tag_configure("bold", font=("SF Pro Text", 13, "bold"))

        # Input bar
        input_frame = ctk.CTkFrame(outer, fg_color="transparent")
        input_frame.pack(fill="x", padx=12, pady=(4, 10))

        self.input_field = ctk.CTkTextbox(
            input_frame, font=("SF Pro Text", 13), fg_color="#1e1e1e",
            text_color="#e0e0e0", border_color="#3a3a3a", border_width=1,
            height=38, corner_radius=10, wrap="word",
        )
        self.input_field.pack(fill="x", side="left", expand=True, padx=(0, 8))
        self.input_field.bind("<Return>", self._on_return)
        self.input_field.bind("<Shift-Return>", lambda e: None)
        self.input_field.bind("<KeyRelease>", self._auto_resize_input)
        self._input_max_height = 120

        self.send_btn = ctk.CTkButton(
            input_frame, text=">", width=45, height=38,
            font=("SF Pro Text", 15, "bold"),
            fg_color="#4cc9f0", hover_color="#3ab4d9", corner_radius=10,
            text_color="#1a1a1a", command=self._on_send,
        )
        self.send_btn.pack(side="right", anchor="s")

        self._append_text("Jarvis", "How can I help?\n", "assistant_label")

    def _on_return(self, event):
        if event.state & 1:  # Shift held
            return
        self._on_send()
        return "break"

    def _auto_resize_input(self, event=None):
        widget = self.input_field._textbox
        widget.update_idletasks()
        count = widget.count("1.0", "end", "displaylines")
        display_lines = max(1, count[0] if count else 1)
        new_height = min(38 + (display_lines - 1) * 20, self._input_max_height)
        self.input_field.configure(height=new_height)
        widget.see("insert")

    def show(self, x, y, animate=True):
        self.geometry(f"{config.WINDOW_WIDTH}x{config.WINDOW_HEIGHT}+{x}+{y}")
        self.deiconify()
        self.lift()
        self.attributes("-alpha", 0.88)
        if not animate:
            self._run_border_trace()
            return
        self._target_x = x
        self._target_y = y
        self._anim_step = 0
        self._anim_total = 12
        slide_offset = 30
        self.attributes("-alpha", 0.0)
        self.geometry(f"{config.WINDOW_WIDTH}x{config.WINDOW_HEIGHT}+{x}+{y + slide_offset}")
        self._animate_show()

    def _run_border_trace(self):
        """Draw a glowing blue border trace over the popup content, then reveal."""
        w, h = config.WINDOW_WIDTH, config.WINDOW_HEIGHT
        overlay = tk.Canvas(self, width=w, height=h, bg=self.BG, highlightthickness=0)
        overlay.place(x=0, y=0)
        self.tk.call('raise', overlay._w)  # raise widget, not canvas item
        self.update_idletasks()

        frame = [0]
        FRAMES = 32
        perimeter = 2 * (w + h)
        segments = [
            (w, h, w, 0, h),   # right edge up
            (w, 0, 0, 0, w),   # top right→left
            (0, 0, 0, h, h),   # left edge down
            (0, h, w, h, w),   # bottom left→right
        ]
        glow_layers = [
            (9, "#0a2535"),
            (5, "#1a7a9a"),
            (2, "#4cc9f0"),
        ]

        def draw_frame():
            frame[0] += 1
            t = frame[0] / FRAMES
            t = 1 - (1 - t) ** 2  # ease-out quad
            progress = t * perimeter

            overlay.delete("trace")
            for line_w, color in glow_layers:
                rem = progress
                px, py = w, h
                for sx, sy, ex, ey, seg_len in segments:
                    if rem <= 0:
                        break
                    frac = min(rem, seg_len) / seg_len
                    cx = sx + (ex - sx) * frac
                    cy = sy + (ey - sy) * frac
                    overlay.create_line(
                        px, py, cx, cy,
                        fill=color, width=line_w, tags="trace",
                        capstyle="round", joinstyle="miter",
                    )
                    px, py = cx, cy
                    rem -= seg_len

            if frame[0] < FRAMES:
                overlay.after(14, draw_frame)
            else:
                overlay.after(80, overlay.destroy)
                overlay.after(80, lambda: self.input_field.focus())

        overlay.after(20, draw_frame)

    def _animate_show(self):
        self._anim_step += 1
        t = self._anim_step / self._anim_total
        t = 1 - (1 - t) ** 3  # ease-out cubic
        slide_offset = 30
        cur_y = int(self._target_y + slide_offset * (1 - t))
        alpha = min(t / 0.88 * 0.88, 0.88)
        self.attributes("-alpha", alpha)
        self.geometry(f"+{self._target_x}+{cur_y}")
        if self._anim_step < self._anim_total:
            self.after(12, self._animate_show)
        else:
            self.attributes("-alpha", 0.88)
            self.geometry(f"+{self._target_x}+{self._target_y}")
            self.after(30, lambda: self.input_field.focus())

    def hide(self):
        self._hide_step = 0
        self._hide_total = 8
        self._hide_y = self.winfo_y()
        self._animate_hide()

    def _animate_hide(self):
        self._hide_step += 1
        t = self._hide_step / self._hide_total
        t = t * t  # ease-in quad
        slide_down = int(20 * t)
        alpha = max(0.88 * (1 - t), 0.0)
        self.attributes("-alpha", alpha)
        self.geometry(f"+{self.winfo_x()}+{self._hide_y + slide_down}")
        if self._hide_step < self._hide_total:
            self.after(12, self._animate_hide)
        else:
            self.withdraw()
            self.attributes("-alpha", 0.88)

    def _on_send(self, event=None):
        if self.is_generating:
            return
        message = self.input_field.get("1.0", "end-1c").strip()
        if not message:
            return

        self.input_field.delete("1.0", "end")
        self.input_field.configure(height=38)
        self._append_text("You", message + "\n", "user_label")

        self.is_generating = True
        self.send_btn.configure(state="disabled", fg_color="#3a3a3a")

        thread = threading.Thread(target=self._generate_response, args=(message,), daemon=True)
        thread.start()

    def _generate_response(self, message):
        self.update_queue.put(("start", None))
        try:
            def on_chunk(text):
                self.update_queue.put(("chunk", text))
            self.agent.chat_stream(message, on_chunk=on_chunk)
            self.update_queue.put(("end", None))
        except Exception as e:
            self.update_queue.put(("error", str(e)))

    # ── Loading spinner ──────────────────────────────────────────────

    def _create_loading_spinner(self):
        size = 20
        canvas = tk.Canvas(
            self.chat_display._textbox,
            width=size, height=size,
            bg=self.BG, highlightthickness=0, bd=0,
        )
        self._spinner = canvas
        self._spinner_angle = 0
        self._spinner_after_id = None
        self._spin()
        return canvas

    def _spin(self):
        c = self._spinner
        c.delete("all")
        a = self._spinner_angle
        for i in range(3):
            start = a + i * 120
            c.create_arc(2, 2, 18, 18, start=start, extent=80,
                         outline="#4cc9f0", width=2, style="arc")
        self._spinner_angle = (a + 10) % 360
        self._spinner_after_id = c.after(40, self._spin)

    def _show_loading(self):
        spinner = self._create_loading_spinner()
        self.chat_display.configure(state="normal")
        self.chat_display._textbox.mark_set("load_start", "end-1c")
        self.chat_display._textbox.mark_gravity("load_start", "left")
        self.chat_display._textbox.window_create("end", window=spinner, padx=4, pady=2)
        self.chat_display._textbox.insert("end", " thinking...", "dim")
        self.chat_display._textbox.mark_set("load_end", "end")
        self.chat_display.configure(state="disabled")
        self.chat_display.see("end")

    def _hide_loading(self):
        if not hasattr(self, "_spinner") or self._spinner is None:
            return
        if self._spinner_after_id:
            self._spinner.after_cancel(self._spinner_after_id)
            self._spinner_after_id = None
        self.chat_display.configure(state="normal")
        try:
            self.chat_display._textbox.delete("load_start", "load_end")
        except tk.TclError:
            pass
        self._spinner.destroy()
        self._spinner = None
        self.chat_display.configure(state="disabled")

    # ── Markdown rendering ─────────────────────────────────────────

    def _render_markdown(self):
        tb = self.chat_display._textbox
        self.chat_display.configure(state="normal")

        # **bold** -> bold tag
        while True:
            open_pos = tb.search("**", "response_start", "end")
            if not open_pos:
                break
            close_pos = tb.search("**", f"{open_pos}+2c", "end")
            if not close_pos:
                break
            bold_text = tb.get(f"{open_pos}+2c", close_pos)
            tb.delete(open_pos, f"{close_pos}+2c")
            tb.insert(open_pos, bold_text, "bold")

        # "* " or "- " at line start -> "• "
        for pattern in (r"^\* ", r"^- "):
            while True:
                pos = tb.search(pattern, "response_start", "end", regexp=True)
                if not pos:
                    break
                tb.delete(pos, f"{pos}+2c")
                tb.insert(pos, "• ")

        self.chat_display.configure(state="disabled")

    # ── Queue processing ──────────────────────────────────────────

    def _process_queue(self):
        try:
            while True:
                msg_type, data = self.update_queue.get_nowait()
                if msg_type == "start":
                    self._append_label("Jarvis", "assistant_label")
                    self.chat_display.configure(state="normal")
                    self.chat_display._textbox.mark_set("response_start", "end-1c")
                    self.chat_display._textbox.mark_gravity("response_start", "left")
                    self.chat_display.configure(state="disabled")
                    self._show_loading()
                    if self.app:
                        self.app.set_anim_state("thinking")
                elif msg_type == "chunk":
                    self._hide_loading()
                    self._append_raw(data)
                elif msg_type == "end":
                    self._hide_loading()
                    self._render_markdown()
                    self._append_raw("\n\n")
                    self.is_generating = False
                    self.send_btn.configure(state="normal", fg_color="#4cc9f0")
                    if self.app:
                        self.app.set_anim_state("listening")
                elif msg_type == "error":
                    self._hide_loading()
                    self._append_raw(f"\n[Error: {data}]\n\n", "error")
                    self.is_generating = False
                    self.send_btn.configure(state="normal", fg_color="#4cc9f0")
                    if self.app:
                        self.app.set_anim_state("listening")
        except queue.Empty:
            pass
        self.after(50, self._process_queue)

    def _sender_prefix(self, sender):
        content = self.chat_display._textbox.get("1.0", "end").strip()
        return f"{sender}: " if not content else f"\n{sender}: "

    def _append_text(self, sender, text, label_tag):
        self.chat_display.configure(state="normal")
        self.chat_display._textbox.insert("end", self._sender_prefix(sender), label_tag)
        self.chat_display._textbox.insert("end", text)
        self.chat_display.configure(state="disabled")
        self.chat_display.see("end")

    def _append_label(self, sender, tag):
        self.chat_display.configure(state="normal")
        self.chat_display._textbox.insert("end", self._sender_prefix(sender), tag)
        self.chat_display.configure(state="disabled")
        self.chat_display.see("end")

    def _append_raw(self, text, tag=None):
        self.chat_display.configure(state="normal")
        if tag:
            self.chat_display._textbox.insert("end", text, tag)
        else:
            self.chat_display._textbox.insert("end", text)
        self.chat_display.configure(state="disabled")
        self.chat_display.see("end")

    def _clear_chat(self):
        self.agent.clear_conversation()
        self.chat_display.configure(state="normal")
        self.chat_display._textbox.delete("1.0", "end")
        self.chat_display.configure(state="disabled")
        self._append_text("Jarvis", "Chat cleared. How can I help?\n", "assistant_label")


class JarvisApp(tk.Tk):
    # outer_step: clockwise gear, inner_step: counter-clockwise segments
    _STATES = {
        "idle": {
            "interval": 50,
            "outer_step": 0.6,  "outer_color": "#2a6a80", "outer_width": 2,
            "inner_step": 1.2,  "inner_color": "#1a4a60", "inner_width": 3,
            "glow_r": 22, "glow_color": "#061520",
        },
        "listening": {
            "interval": 30,
            "outer_step": 1.5,  "outer_color": "#7acce0", "outer_width": 2,
            "inner_step": 3.0,  "inner_color": "#4cc9f0", "inner_width": 3,
            "glow_r": 26, "glow_color": "#082030",
        },
        "thinking": {
            "interval": 15,
            "outer_step": 3.0,  "outer_color": "#b0e4f4", "outer_width": 2,
            "inner_step": 6.0,  "inner_color": "#ffffff", "inner_width": 3,
            "glow_r": 30, "glow_color": "#0d2f42",
        },
    }

    def __init__(self, agent):
        super().__init__()
        ctk.set_appearance_mode("dark")
        self.agent = agent
        self.popup = None
        self.popup_visible = False
        self._drag_x = 0
        self._drag_y = 0
        self._anim_state = "idle"
        self._outer_angle = 0.0   # gear ring, clockwise
        self._inner_angle = 0.0   # segment ring, counter-clockwise
        self._pulse_tick = 0
        self._setup_window()
        self._create_icon_canvas()
        self._animate_rings()

    def _setup_window(self):
        icon_sz = config.ICON_SIZE
        self.geometry(f"{icon_sz}x{icon_sz}")
        self.title("Jarvis")
        self.overrideredirect(True)
        self.wm_attributes("-transparent", True)
        self.config(bg="systemTransparent")
        self.after(100, self._position_bottom_right)

    def _position_bottom_right(self):
        self.update_idletasks()
        icon_sz = config.ICON_SIZE
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        x = screen_w - icon_sz - 30
        y = screen_h - icon_sz - 80
        self.geometry(f"{icon_sz}x{icon_sz}+{x}+{y}")

    def _create_icon_canvas(self):
        icon_path = Path(__file__).parent.parent / "assets" / "icon.png"
        icon_sz = config.ICON_SIZE
        img_sz = icon_sz - 40  # leave 20px each side for the two rings
        img = Image.open(icon_path)
        bbox = img.getbbox()
        if bbox:
            img = img.crop(bbox)
        img = img.resize((img_sz, img_sz), Image.LANCZOS)
        self.icon_photo = ImageTk.PhotoImage(img)

        self.icon_canvas = tk.Canvas(
            self, width=icon_sz, height=icon_sz,
            bg="systemTransparent", highlightthickness=0, bd=0, cursor="hand2",
        )
        self.icon_canvas.place(x=0, y=0)
        self.icon_canvas.create_image(icon_sz // 2, icon_sz // 2,
                                      image=self.icon_photo, anchor="center", tags="icon")
        self.icon_canvas.bind("<Button-1>", self._on_press)
        self.icon_canvas.bind("<B1-Motion>", self._on_drag)
        self.icon_canvas.bind("<ButtonRelease-1>", self._on_release)

    # ── Animation ─────────────────────────────────────────────────

    def set_anim_state(self, state):
        self._anim_state = state

    def _animate_rings(self):
        cfg = self._STATES[self._anim_state]
        sz = config.ICON_SIZE
        cx = cy = sz // 2

        pulse = math.sin(self._pulse_tick * 0.1)
        self._pulse_tick += 1

        # ── Glow behind image ──────────────────────────────────────
        glow_r = cfg["glow_r"] + int(pulse * 2)
        self.icon_canvas.delete("glow")
        self.icon_canvas.create_oval(
            cx - glow_r, cy - glow_r, cx + glow_r, cy + glow_r,
            fill=cfg["glow_color"], outline="", tags="glow",
        )
        self.icon_canvas.tag_lower("glow", "icon")

        # ── Inner bright ring (counter-clockwise, chunky segments) ─
        # sits just outside the image (image radius ≈ 25, ring at 30)
        inner_r = 30
        n_inner_segs = 12
        inner_extent = 20
        inner_gap = (360 / n_inner_segs) - inner_extent  # 10°
        self.icon_canvas.delete("inner_ring")
        for seg in range(n_inner_segs):
            start = self._inner_angle + seg * (inner_extent + inner_gap)
            self.icon_canvas.create_arc(
                cx - inner_r, cy - inner_r, cx + inner_r, cy + inner_r,
                start=start, extent=inner_extent,
                outline=cfg["inner_color"], width=cfg["inner_width"],
                style="arc", tags="inner_ring",
            )

        # ── Outer gear ring (clockwise, fine teeth) ────────────────
        # outermost, close to canvas edge
        outer_r = 42
        n_teeth = 48
        tooth_extent = 4.5
        tooth_gap = (360 / n_teeth) - tooth_extent  # ≈ 3°
        self.icon_canvas.delete("outer_ring")
        for tooth in range(n_teeth):
            start = self._outer_angle + tooth * (tooth_extent + tooth_gap)
            self.icon_canvas.create_arc(
                cx - outer_r, cy - outer_r, cx + outer_r, cy + outer_r,
                start=start, extent=tooth_extent,
                outline=cfg["outer_color"], width=cfg["outer_width"],
                style="arc", tags="outer_ring",
            )

        # Advance angles
        self._inner_angle = (self._inner_angle - cfg["inner_step"]) % 360
        self._outer_angle = (self._outer_angle + cfg["outer_step"]) % 360

        self.after(cfg["interval"], self._animate_rings)

    # ── Drag & click ──────────────────────────────────────────────

    def _on_press(self, event):
        self._drag_x = event.x
        self._drag_y = event.y
        self._dragged = False

    def _on_drag(self, event):
        dx = abs(event.x - self._drag_x)
        dy = abs(event.y - self._drag_y)
        if dx > 5 or dy > 5:
            self._dragged = True
        if self._dragged:
            x = self.winfo_x() + event.x - self._drag_x
            y = self.winfo_y() + event.y - self._drag_y
            self.geometry(f"+{x}+{y}")

    def _on_release(self, event):
        if not self._dragged:
            self.toggle_popup()

    def toggle_popup(self):
        if self.popup is None:
            self.popup = ChatPopup(self, self.agent, app=self)

        if self.popup_visible:
            self.popup.hide()
            self.popup_visible = False
            self.set_anim_state("idle")
        else:
            ix = self.winfo_x()
            iy = self.winfo_y()
            popup_x = ix + config.ICON_SIZE - config.WINDOW_WIDTH
            popup_y = iy - config.WINDOW_HEIGHT - 50
            if popup_x < 0:
                popup_x = 0
            if popup_y < 0:
                popup_y = iy + config.ICON_SIZE + 15
            self.popup_visible = True
            self.set_anim_state("listening")
            self.popup.show(popup_x, popup_y, animate=False)

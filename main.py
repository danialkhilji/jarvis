import sys
import threading

import config
from assistant import AgnoAssistant
from ui.popup import JarvisApp


def write_confirm(path, content):
    import customtkinter as ctk

    result = {"confirmed": False}
    event = threading.Event()

    def show_dialog():
        try:
            dialog = ctk.CTkToplevel(app)
            dialog.title("Confirm File Write")
            dialog.geometry("500x350")
            dialog.attributes("-topmost", True)
            dialog.focus_force()
            dialog.after(100, lambda: dialog.grab_set())

            ctk.CTkLabel(
                dialog, text=f"Write to:\n{path}",
                font=("Helvetica", 13, "bold"), wraplength=460, justify="left",
            ).pack(pady=(15, 5), padx=15, anchor="w")

            preview = ctk.CTkTextbox(dialog, height=200, font=("Courier", 11))
            preview.pack(fill="both", expand=True, padx=15, pady=5)
            display = content[:2000] + ("\n..." if len(content) > 2000 else "")
            preview.insert("1.0", display)
            preview.configure(state="disabled")

            btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
            btn_frame.pack(fill="x", padx=15, pady=10)

            def allow():
                result["confirmed"] = True
                dialog.grab_release()
                dialog.destroy()
                event.set()

            def deny():
                dialog.grab_release()
                dialog.destroy()
                event.set()

            ctk.CTkButton(btn_frame, text="Allow", fg_color="#4ecca3", hover_color="#3ba88a", command=allow).pack(side="right", padx=5)
            ctk.CTkButton(btn_frame, text="Deny", fg_color="#e94560", hover_color="#c73850", command=deny).pack(side="right", padx=5)

            dialog.protocol("WM_DELETE_WINDOW", deny)
        except Exception as e:
            print(f"Error showing write confirm dialog: {e}")
            event.set()

    app.after(0, show_dialog)
    event.wait(timeout=120)
    return result["confirmed"]



def main():
    global app

    if not config.GROQ_API_KEY:
        print("Error: GROQ_API_KEY not set.")
        print(f"Create a .env file in {config.BASE_DIR} with:")
        print("  GROQ_API_KEY=your_key_here")
        print("\nGet a free API key at: https://console.groq.com/keys")
        sys.exit(1)

    assistant = AgnoAssistant(write_confirm_callback=write_confirm)
    app = JarvisApp(assistant)

    print("Jarvis is running...")
    app.mainloop()


if __name__ == "__main__":
    main()

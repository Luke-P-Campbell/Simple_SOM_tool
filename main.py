import tkinter as tk
from PIL import Image, ImageTk, ImageDraw, ImageFont
import global_vars,misc,neighbourhood,weights,analysis
import os


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Self Organising Map Tool")
        self.root.geometry("1200x700")
        self.root.minsize(600, 400)

        big_comms_dict = {**global_vars.comms, **misc.comms, **neighbourhood.comms, **weights.comms, **analysis.comms}
        self.comms = {key: value[0] for key, value in big_comms_dict.items()}
        description = "\n\n".join(value[1] for value in big_comms_dict.values()) + "\n"
        def help_func(app,args):
                app.write(description)
        self.comms["help"] = help_func

        self.paned = tk.PanedWindow(
            root,
            orient=tk.HORIZONTAL,
            sashwidth=4,
            showhandle=False,
            bd=0,
            bg="#888888"
        )
        self.paned.pack(fill=tk.BOTH, expand=True)

        self.cli_frame = tk.Frame(self.paned, bg="#111111")

        self.image_frame = tk.Frame(self.paned, bg="white")

        self.paned.add(self.cli_frame, stretch="always")
        self.paned.add(self.image_frame, stretch="always")

        self.cli = tk.Text(
            self.cli_frame,
            bg="#111111",
            fg="#eeeeee",
            insertbackground="white",
            font=("Consolas", 11),
            bd=0,
            padx=10,
            pady=10,
            wrap=tk.WORD
        )
        self.cli.pack(fill=tk.BOTH, expand=True)

        self.cli.bind("<Return>", self.handle_command)

        self.write("> ")

        self.canvas = tk.Canvas(
            self.image_frame,
            bg="white",
            highlightthickness=0
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.original_image = None
        self.display_image = None

        self.create_blank_image()

        self.canvas.bind("<Configure>", self.on_canvas_resize)

        self.root.after(100, self.set_half_split)
        self.root.bind("<Configure>", self.on_window_resize)

    def set_half_split(self):
        width = self.root.winfo_width()

        if width > 1:
            self.paned.sash_place(0, width // 2, 0)

    def on_window_resize(self, event):
        if event.widget == self.root:
            self.root.after_idle(self.set_half_split)

    def write(self, text):
        self.cli.insert(tk.END, text)
        self.cli.see(tk.END)

    def handle_command(self, event=None):
        if event:
            event.widget.mark_set("insert", "end-1c")

        line = self.cli.get("end-1c linestart", "end-1c").strip()

        if line.startswith("> "):
            command = line[2:]
        else:
            command = line

        self.write("\n")

        if command:
            self.run_command(command)

        self.write("> ")

        return "break"

    def run_command(self, command):
        parts = command.split(maxsplit=1)

        if not parts:
            return

        cmd = parts[0].lower()

        args = parts[1].split() if len(parts) > 1 else []

        function = self.comms.get(cmd)

        if function is None:
            self.write(f"Unknown command: {cmd}\n")
            return

        function(self, args)

    def create_blank_image(self):
        width = 1000
        height = 600

        image = Image.new(
            "RGB",
            (width, height),
            "white"
        )

        image.save("image.png")

        self.original_image = image
        self.render_image()

    def create_echo_image(self, text):
        width = 1000
        height = 600

        image = Image.new(
            "RGB",
            (width, height),
            "white"
        )

        draw = ImageDraw.Draw(image)

        try:
            font = ImageFont.truetype("arial.ttf", 100)
        except OSError:
            font = ImageFont.load_default()

        bbox = draw.textbbox(
            (0, 0),
            text,
            font=font
        )

        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        x = (width - text_width) // 2
        y = (height - text_height) // 2

        draw.text(
            (x, y),
            text,
            fill="black",
            font=font
        )

        image.save("image.png")

        self.original_image = image
        self.render_image()

    def load_image(self, filename):
        try:
            image = Image.open(filename).convert("RGB")

            self.original_image = image
            self.render_image()

        except Exception as e:
            self.write(f"Could not load image: {e}\n")
            self.create_blank_image()

    def on_canvas_resize(self, event=None):
        self.render_image()

    def render_image(self):
        if self.original_image is None:
            return

        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        if canvas_width <= 1 or canvas_height <= 1:
            return

        image_width, image_height = self.original_image.size

        scale = min(
            canvas_width / image_width,
            canvas_height / image_height
        )

        new_width = max(1, int(image_width * scale))
        new_height = max(1, int(image_height * scale))

        resized = self.original_image.resize(
            (new_width, new_height),
            Image.Resampling.LANCZOS
        )

        self.display_image = ImageTk.PhotoImage(resized)

        self.canvas.delete("all")

        self.canvas.create_image(
            canvas_width // 2,
            canvas_height // 2,
            image=self.display_image,
            anchor=tk.CENTER
        )


if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()

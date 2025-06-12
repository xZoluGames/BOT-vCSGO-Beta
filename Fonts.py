import tkinter as tk
import tkinter.font as font

def display_fonts():
    # Crear la ventana principal
    root = tk.Tk()
    root.title("Available Fonts")
    root.geometry("430x600")  # Ajustar el tamaño de la ventana

    # Crear un canvas para mostrar las fuentes
    canvas = tk.Canvas(root)
    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    # Agregar un scrollbar
    scrollbar = tk.Scrollbar(root, orient="vertical", command=canvas.yview)
    scrollbar.pack(side="right", fill="y")

    # Crear un frame que contendrá las fuentes
    frame = tk.Frame(canvas)
    canvas.create_window((0, 0), window=frame, anchor="nw")

    # Agregar el scrollbar al canvas
    canvas.configure(yscrollcommand=scrollbar.set)

    # Agregar texto en diferentes fuentes y centrarlos
    for font_name in font.families():
        label = tk.Label(frame, text=f"{font_name}", font=(font_name, 18))
        label.pack(pady=5, padx=20)  # Padding para el espaciado
        label.config(anchor="center")  # Centrar el texto

    # Actualizar el tamaño del canvas al contenido
    frame.update_idletasks()
    canvas.config(scrollregion=canvas.bbox("all"))

    # Configurar el tamaño mínimo de la ventana
    root.minsize(400, 400)

    # Ejecutar el bucle principal
    root.mainloop()

if __name__ == "__main__":
    display_fonts()


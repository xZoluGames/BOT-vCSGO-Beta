#!/usr/bin/env python3
# gui_modern.py - Interfaz gráfica moderna para BOT-vCSGO-Beta

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import json
import time
from datetime import datetime
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent))

from backend.core.config_manager import get_config_manager
from backend.services.database_service import get_database_service
from backend.services.notification_service import get_notification_service
from backend.services.profitability_service import ProfitabilityService
import subprocess


class ModernCSGOBot:
    def __init__(self, root):
        self.root = root
        self.root.title("BOT-vCSGO-Beta v2.0 - Panel de Control")
        self.root.geometry("1200x700")
        
        # Configurar estilo moderno
        self.setup_styles()
        
        # Servicios
        self.config_manager = get_config_manager()
        self.db_service = get_database_service()
        self.notification_service = get_notification_service()
        
        # Variables
        self.processes = {}
        self.is_monitoring = False
        
        # Crear interfaz
        self.create_widgets()
        
        # Actualizar estado inicial
        self.update_status()
        
        # Iniciar actualizaciones automáticas
        self.auto_update()
    
    def setup_styles(self):
        """Configura estilos modernos para la interfaz"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Colores
        self.colors = {
            'bg': '#1e1e1e',
            'fg': '#ffffff',
            'accent': '#00d4ff',
            'success': '#00ff88',
            'warning': '#ffaa00',
            'error': '#ff5555',
            'panel': '#2d2d2d',
            'button': '#3d3d3d'
        }
        
        # Configurar estilos
        style.configure('Title.TLabel', font=('Arial', 16, 'bold'))
        style.configure('Heading.TLabel', font=('Arial', 12, 'bold'))
        
        self.root.configure(bg=self.colors['bg'])
    
    def create_widgets(self):
        """Crea todos los widgets de la interfaz"""
        # Frame principal
        main_frame = tk.Frame(self.root, bg=self.colors['bg'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Panel superior - Estado y controles
        self.create_top_panel(main_frame)
        
        # Panel central - Notebook con pestañas
        self.create_center_panel(main_frame)
        
        # Panel inferior - Estado y logs
        self.create_bottom_panel(main_frame)
    
    def create_top_panel(self, parent):
        """Crea el panel superior con controles principales"""
        top_frame = tk.Frame(parent, bg=self.colors['panel'], height=100)
        top_frame.pack(fill=tk.X, pady=(0, 10))
        top_frame.pack_propagate(False)
        
        # Título
        title_label = tk.Label(
            top_frame, 
            text="🎮 BOT-vCSGO-Beta - Sistema de Arbitraje",
            font=('Arial', 18, 'bold'),
            bg=self.colors['panel'],
            fg=self.colors['accent']
        )
        title_label.pack(pady=10)
        
        # Frame de controles
        controls_frame = tk.Frame(top_frame, bg=self.colors['panel'])
        controls_frame.pack()
        
        # Botones principales
        self.monitor_btn = tk.Button(
            controls_frame,
            text="▶ INICIAR MONITOR",
            command=self.toggle_monitor,
            bg=self.colors['success'],
            fg='black',
            font=('Arial', 12, 'bold'),
            width=20,
            height=2
        )
        self.monitor_btn.grid(row=0, column=0, padx=5)
        
        tk.Button(
            controls_frame,
            text="📊 ANÁLISIS RÁPIDO",
            command=self.run_quick_analysis,
            bg=self.colors['accent'],
            fg='black',
            font=('Arial', 12, 'bold'),
            width=20,
            height=2
        ).grid(row=0, column=1, padx=5)
        
        tk.Button(
            controls_frame,
            text="⚙️ CONFIGURACIÓN",
            command=self.open_settings,
            bg=self.colors['button'],
            fg='white',
            font=('Arial', 12, 'bold'),
            width=20,
            height=2
        ).grid(row=0, column=2, padx=5)
    
    def create_center_panel(self, parent):
        """Crea el panel central con pestañas"""
        # Notebook para pestañas
        self.notebook = ttk.Notebook(parent)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Pestaña de Oportunidades
        self.create_opportunities_tab()
        
        # Pestaña de Scrapers
        self.create_scrapers_tab()
        
        # Pestaña de Estadísticas
        self.create_stats_tab()
        
        # Pestaña de Notificaciones
        self.create_notifications_tab()
    
    def create_opportunities_tab(self):
        """Crea la pestaña de oportunidades rentables"""
        frame = tk.Frame(self.notebook, bg=self.colors['bg'])
        self.notebook.add(frame, text="💰 Oportunidades")
        
        # Treeview para mostrar oportunidades
        columns = ('Item', 'Comprar En', 'Precio', 'Rentabilidad', 'Ganancia')
        self.opp_tree = ttk.Treeview(frame, columns=columns, show='headings', height=15)
        
        # Configurar columnas
        for col in columns:
            self.opp_tree.heading(col, text=col)
            self.opp_tree.column(col, width=200)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.opp_tree.yview)
        self.opp_tree.configure(yscrollcommand=scrollbar.set)
        
        # Empaquetar
        self.opp_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Botones de acción
        action_frame = tk.Frame(frame, bg=self.colors['bg'])
        action_frame.pack(fill=tk.X, pady=5)
        
        tk.Button(
            action_frame,
            text="🔄 Actualizar",
            command=self.update_opportunities,
            bg=self.colors['button'],
            fg='white'
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            action_frame,
            text="📋 Copiar Selección",
            command=self.copy_opportunity,
            bg=self.colors['button'],
            fg='white'
        ).pack(side=tk.LEFT, padx=5)
    
    def create_scrapers_tab(self):
        """Crea la pestaña de estado de scrapers"""
        frame = tk.Frame(self.notebook, bg=self.colors['bg'])
        self.notebook.add(frame, text="🤖 Scrapers")
        
        # Frame para controles de scrapers
        self.scrapers_frame = tk.Frame(frame, bg=self.colors['bg'])
        self.scrapers_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Lista de scrapers principales
        scrapers = ['waxpeer', 'csdeals', 'empire', 'skinport', 'steammarket']
        
        for i, scraper in enumerate(scrapers):
            self.create_scraper_control(self.scrapers_frame, scraper, i)
    
    def create_scraper_control(self, parent, scraper_name, row):
        """Crea controles para un scraper individual"""
        frame = tk.Frame(parent, bg=self.colors['panel'], relief=tk.RAISED, bd=1)
        frame.grid(row=row, column=0, sticky='ew', pady=2, padx=5)
        parent.grid_columnconfigure(0, weight=1)
        
        # Nombre del scraper
        tk.Label(
            frame,
            text=scraper_name.upper(),
            font=('Arial', 10, 'bold'),
            bg=self.colors['panel'],
            fg='white',
            width=15
        ).pack(side=tk.LEFT, padx=10)
        
        # Estado
        status_label = tk.Label(
            frame,
            text="⚫ Detenido",
            bg=self.colors['panel'],
            fg=self.colors['warning'],
            width=15
        )
        status_label.pack(side=tk.LEFT, padx=10)
        
        # Botones
        tk.Button(
            frame,
            text="▶",
            command=lambda s=scraper_name: self.start_scraper(s),
            bg=self.colors['success'],
            fg='black',
            width=3
        ).pack(side=tk.LEFT, padx=2)
        
        tk.Button(
            frame,
            text="⏹",
            command=lambda s=scraper_name: self.stop_scraper(s),
            bg=self.colors['error'],
            fg='white',
            width=3
        ).pack(side=tk.LEFT, padx=2)
        
        # Guardar referencia al label de estado
        setattr(self, f"{scraper_name}_status", status_label)
    
    def create_stats_tab(self):
        """Crea la pestaña de estadísticas"""
        frame = tk.Frame(self.notebook, bg=self.colors['bg'])
        self.notebook.add(frame, text="📊 Estadísticas")
        
        # Frame de estadísticas
        stats_frame = tk.Frame(frame, bg=self.colors['panel'])
        stats_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Etiquetas de estadísticas
        self.stats_labels = {}
        stats = [
            ('total_items', 'Items Totales:'),
            ('total_opportunities', 'Oportunidades Activas:'),
            ('best_profit', 'Mejor Rentabilidad:'),
            ('avg_profit', 'Rentabilidad Promedio:'),
            ('last_update', 'Última Actualización:')
        ]
        
        for i, (key, text) in enumerate(stats):
            tk.Label(
                stats_frame,
                text=text,
                font=('Arial', 12),
                bg=self.colors['panel'],
                fg='white'
            ).grid(row=i, column=0, sticky='w', padx=20, pady=5)
            
            label = tk.Label(
                stats_frame,
                text="--",
                font=('Arial', 12, 'bold'),
                bg=self.colors['panel'],
                fg=self.colors['accent']
            )
            label.grid(row=i, column=1, sticky='w', padx=20, pady=5)
            self.stats_labels[key] = label
    
    def create_notifications_tab(self):
        """Crea la pestaña de notificaciones"""
        frame = tk.Frame(self.notebook, bg=self.colors['bg'])
        self.notebook.add(frame, text="🔔 Notificaciones")
        
        # Text widget para notificaciones
        self.notifications_text = scrolledtext.ScrolledText(
            frame,
            wrap=tk.WORD,
            bg=self.colors['panel'],
            fg='white',
            font=('Consolas', 10),
            height=20
        )
        self.notifications_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Botón para limpiar
        tk.Button(
            frame,
            text="🗑️ Limpiar Notificaciones",
            command=self.clear_notifications,
            bg=self.colors['button'],
            fg='white'
        ).pack(pady=5)
    
    def create_bottom_panel(self, parent):
        """Crea el panel inferior con logs"""
        bottom_frame = tk.Frame(parent, bg=self.colors['panel'], height=150)
        bottom_frame.pack(fill=tk.BOTH, expand=True)
        bottom_frame.pack_propagate(False)
        
        # Label para logs
        tk.Label(
            bottom_frame,
            text="📝 Logs del Sistema",
            font=('Arial', 10, 'bold'),
            bg=self.colors['panel'],
            fg='white'
        ).pack(anchor='w', padx=10, pady=5)
        
        # Text widget para logs
        self.log_text = scrolledtext.ScrolledText(
            bottom_frame,
            wrap=tk.WORD,
            bg='black',
            fg='white',
            font=('Consolas', 9),
            height=8
        )
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
    
    # Métodos de funcionalidad
    def toggle_monitor(self):
        """Inicia o detiene el monitor"""
        if not self.is_monitoring:
            self.start_monitor()
        else:
            self.stop_monitor()
    
    def start_monitor(self):
        """Inicia el monitor en un thread separado"""
        self.is_monitoring = True
        self.monitor_btn.configure(
            text="⏹ DETENER MONITOR",
            bg=self.colors['error']
        )
        self.log("Monitor iniciado")
        
        # Iniciar proceso de monitor
        def run_monitor():
            try:
                subprocess.run([sys.executable, "run_scrapers.py", "monitor"])
            except Exception as e:
                self.log(f"Error en monitor: {e}", "error")
        
        self.monitor_thread = threading.Thread(target=run_monitor, daemon=True)
        self.monitor_thread.start()
    
    def stop_monitor(self):
        """Detiene el monitor"""
        self.is_monitoring = False
        self.monitor_btn.configure(
            text="▶ INICIAR MONITOR",
            bg=self.colors['success']
        )
        self.log("Monitor detenido")
    
    def run_quick_analysis(self):
        """Ejecuta un análisis rápido de rentabilidad"""
        self.log("Ejecutando análisis rápido...")
        
        def analyze():
            try:
                service = ProfitabilityService()
                service.run()
                self.log("Análisis completado", "success")
                self.update_opportunities()
                self.update_stats()
            except Exception as e:
                self.log(f"Error en análisis: {e}", "error")
        
        threading.Thread(target=analyze, daemon=True).start()
    
    def start_scraper(self, scraper_name):
        """Inicia un scraper individual"""
        self.log(f"Iniciando {scraper_name}...")
        
        def run():
            try:
                process = subprocess.Popen(
                    [sys.executable, "run_scrapers.py", scraper_name, "--once"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                self.processes[scraper_name] = process
                
                # Actualizar estado
                status_label = getattr(self, f"{scraper_name}_status", None)
                if status_label:
                    status_label.configure(
                        text="🟢 Ejecutando",
                        fg=self.colors['success']
                    )
                
                # Esperar a que termine
                process.wait()
                
                # Actualizar estado final
                if status_label:
                    status_label.configure(
                        text="⚫ Completado",
                        fg=self.colors['warning']
                    )
                
                self.log(f"{scraper_name} completado", "success")
                
            except Exception as e:
                self.log(f"Error en {scraper_name}: {e}", "error")
        
        threading.Thread(target=run, daemon=True).start()
    
    def stop_scraper(self, scraper_name):
        """Detiene un scraper"""
        if scraper_name in self.processes:
            self.processes[scraper_name].terminate()
            del self.processes[scraper_name]
            
            status_label = getattr(self, f"{scraper_name}_status", None)
            if status_label:
                status_label.configure(
                    text="⚫ Detenido",
                    fg=self.colors['warning']
                )
            
            self.log(f"{scraper_name} detenido")
    
    def update_opportunities(self):
        """Actualiza la lista de oportunidades"""
        try:
            # Limpiar tabla
            for item in self.opp_tree.get_children():
                self.opp_tree.delete(item)
            
            # Obtener oportunidades de la base de datos
            opportunities = self.db_service.get_profitable_opportunities(limit=50)
            
            # Agregar a la tabla
            for opp in opportunities:
                self.opp_tree.insert('', 'end', values=(
                    opp['name'],
                    opp['buy_platform'],
                    f"${opp['buy_price']:.2f}",
                    f"{opp['profit_percentage']:.1f}%",
                    f"${opp['profit_amount']:.2f}"
                ))
            
            self.log(f"Actualizado: {len(opportunities)} oportunidades")
            
        except Exception as e:
            self.log(f"Error actualizando oportunidades: {e}", "error")
    
    def update_stats(self):
        """Actualiza las estadísticas"""
        try:
            # Obtener estadísticas de la BD
            session = self.db_service.db_manager.get_session()
            from backend.database.models import Item, ProfitableOpportunity
            
            total_items = session.query(Item).count()
            total_opps = session.query(ProfitableOpportunity).filter_by(is_active=True).count()
            
            # Mejor rentabilidad
            best = session.query(ProfitableOpportunity).filter_by(
                is_active=True
            ).order_by(ProfitableOpportunity.profitability.desc()).first()
            
            best_profit = f"{best.profitability * 100:.1f}%" if best else "N/A"
            
            session.close()
            
            # Actualizar labels
            self.stats_labels['total_items'].configure(text=str(total_items))
            self.stats_labels['total_opportunities'].configure(text=str(total_opps))
            self.stats_labels['best_profit'].configure(text=best_profit)
            self.stats_labels['last_update'].configure(
                text=datetime.now().strftime("%H:%M:%S")
            )
            
        except Exception as e:
            self.log(f"Error actualizando estadísticas: {e}", "error")
    
    def update_notifications(self):
        """Actualiza la pestaña de notificaciones"""
        try:
            recent = self.notification_service.get_recent_notifications(limit=20)
            
            self.notifications_text.delete(1.0, tk.END)
            
            for notif in reversed(recent):
                timestamp = notif.get('timestamp', '')
                title = notif.get('title', '')
                message = notif.get('message', '')
                level = notif.get('level', 'INFO')
                
                # Color según nivel
                tag = level.lower()
                
                self.notifications_text.insert(tk.END, f"[{timestamp}] ", 'timestamp')
                self.notifications_text.insert(tk.END, f"{title}\n", tag)
                self.notifications_text.insert(tk.END, f"{message}\n\n", 'normal')
            
            # Configurar tags de colores
            self.notifications_text.tag_config('timestamp', foreground='gray')
            self.notifications_text.tag_config('info', foreground=self.colors['accent'])
            self.notifications_text.tag_config('warning', foreground=self.colors['warning'])
            self.notifications_text.tag_config('opportunity', foreground=self.colors['success'])
            
        except Exception as e:
            self.log(f"Error actualizando notificaciones: {e}", "error")
    
    def clear_notifications(self):
        """Limpia las notificaciones"""
        self.notifications_text.delete(1.0, tk.END)
        self.log("Notificaciones limpiadas")
    
    def copy_opportunity(self):
        """Copia la oportunidad seleccionada al portapapeles"""
        selection = self.opp_tree.selection()
        if selection:
            item = self.opp_tree.item(selection[0])
            values = item['values']
            text = f"{values[0]} - Comprar en {values[1]} por {values[2]} - Rentabilidad: {values[3]}"
            
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            self.log("Copiado al portapapeles")
    
    def open_settings(self):
        """Abre la ventana de configuración"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Configuración")
        settings_window.geometry("400x300")
        settings_window.configure(bg=self.colors['bg'])
        
        # Por ahora solo un mensaje
        tk.Label(
            settings_window,
            text="Configuración en desarrollo...\n\nPuedes editar manualmente:\nconfig/settings.json",
            font=('Arial', 12),
            bg=self.colors['bg'],
            fg='white'
        ).pack(expand=True)
    
    def update_status(self):
        """Actualiza el estado general de la aplicación"""
        self.update_opportunities()
        self.update_stats()
        self.update_notifications()
    
    def auto_update(self):
        """Actualiza automáticamente la interfaz cada 30 segundos"""
        self.update_status()
        self.root.after(30000, self.auto_update)  # 30 segundos
    
    def log(self, message, level="info"):
        """Agrega un mensaje al log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Colores según nivel
        colors = {
            'info': 'white',
            'success': self.colors['success'],
            'warning': self.colors['warning'],
            'error': self.colors['error']
        }
        
        self.log_text.insert(tk.END, f"[{timestamp}] ", 'timestamp')
        self.log_text.insert(tk.END, f"{message}\n", level)
        
        # Configurar tags
        self.log_text.tag_config('timestamp', foreground='gray')
        for lvl, color in colors.items():
            self.log_text.tag_config(lvl, foreground=color)
        
        # Auto-scroll
        self.log_text.see(tk.END)


def main():
    """Función principal"""
    root = tk.Tk()
    app = ModernCSGOBot(root)
    
    # Centrar ventana
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (1200 // 2)
    y = (root.winfo_screenheight() // 2) - (700 // 2)
    root.geometry(f"1200x700+{x}+{y}")
    
    root.mainloop()


if __name__ == "__main__":
    main()
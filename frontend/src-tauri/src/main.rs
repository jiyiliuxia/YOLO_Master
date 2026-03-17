// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::process::Command;
use std::thread;
use std::time::Duration;
use tauri::{Manager, RunEvent};

fn main() {
    // ── Launch FastAPI backend in dev mode ───────────────────────────────
    // In production, this would be replaced by a Tauri sidecar.
    // For now we check if uvicorn is already running; if not, start it.
    #[cfg(debug_assertions)]
    {
        thread::spawn(|| {
            // Small delay to let Tauri window initialize first
            thread::sleep(Duration::from_millis(500));

            // Try to connect to backend; if it's already up, do nothing
            let already_running = std::net::TcpStream::connect("127.0.0.1:8765").is_ok();
            if !already_running {
                println!("[YOLOStudio] Starting FastAPI backend...");
                let _ = Command::new("python")
                    .args(["-m", "uvicorn", "backend.main:app",
                           "--host", "127.0.0.1", "--port", "8765"])
                    .current_dir(std::env::current_dir().unwrap().parent().unwrap())
                    .spawn();
            } else {
                println!("[YOLOStudio] Backend already running on :8765");
            }
        });
    }

    let app = tauri::Builder::default()
        .setup(|_app| {
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![])
        .build(tauri::generate_context!())
        .expect("error while building tauri application");

    app.run(|_app_handle, event| {
        if let RunEvent::ExitRequested { .. } = event {
            // Cleanup on exit — kill spawned backend process if needed
        }
    });
}

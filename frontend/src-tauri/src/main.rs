// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::process::{Child, Command};
use std::sync::{Arc, Mutex};
use std::thread;
use std::time::Duration;
use tauri::{Manager, RunEvent};

fn main() {
    // 存储后端进程句柄，关闭时用于 kill
    let backend_child: Arc<Mutex<Option<Child>>> = Arc::new(Mutex::new(None));
    let backend_child_clone = backend_child.clone();

    // ── 开发模式：调用系统 Python 启动 FastAPI ─────────────────────
    #[cfg(debug_assertions)]
    {
        thread::spawn(|| {
            thread::sleep(Duration::from_millis(500));
            let already_running = std::net::TcpStream::connect("127.0.0.1:8765").is_ok();
            if !already_running {
                println!("[YOLOStudio] 开发模式：启动 FastAPI 后端...");
                let _ = Command::new("python")
                    .args(["-m", "uvicorn", "backend.main:app",
                           "--host", "127.0.0.1", "--port", "8765"])
                    .current_dir(
                        std::env::current_dir().unwrap().parent().unwrap()
                    )
                    .spawn();
            } else {
                println!("[YOLOStudio] 后端已在 :8765 运行");
            }
        });
    }

    // ── 生产模式：启动打包后的 backend.exe ────────────────────────
    #[cfg(not(debug_assertions))]
    {
        let child_ref = backend_child.clone();
        thread::spawn(move || {
            // 获取 backend.exe 路径：与当前 exe 同级的 backend\ 子目录
            let exe_dir = std::env::current_exe()
                .unwrap()
                .parent()
                .unwrap()
                .to_path_buf();
            let backend_exe = exe_dir.join("backend").join("backend.exe");

            println!("[YOLOStudio] 生产模式：启动后端 {:?}", backend_exe);

            if !backend_exe.exists() {
                eprintln!("[YOLOStudio] 错误：找不到 backend.exe，路径={:?}", backend_exe);
                return;
            }

            // 已有后端时不重复启动
            if std::net::TcpStream::connect("127.0.0.1:8765").is_ok() {
                println!("[YOLOStudio] 后端已在 :8765 运行，跳过启动");
                return;
            }

            match Command::new(&backend_exe).spawn() {
                Ok(child) => {
                    println!("[YOLOStudio] 后端进程已启动 PID={}", child.id());
                    *child_ref.lock().unwrap() = Some(child);
                }
                Err(e) => {
                    eprintln!("[YOLOStudio] 后端启动失败：{}", e);
                }
            }
        });
    }

    let app = tauri::Builder::default()
        .setup(|_app| Ok(()))
        .invoke_handler(tauri::generate_handler![])
        .build(tauri::generate_context!())
        .expect("构建 Tauri 应用时出错");

    app.run(move |_app_handle, event| {
        if let RunEvent::ExitRequested { .. } = event {
            // 应用退出时，终止后端进程
            if let Ok(mut guard) = backend_child_clone.lock() {
                if let Some(ref mut child) = *guard {
                    println!("[YOLOStudio] 正在关闭后端进程...");
                    let _ = child.kill();
                }
            }
        }
    });
}

<div align="center">

<img src="../assets/svision-logo.png" alt="SVISION Logo" width="120" />

# SVISION — Комплект технической документации
### Synapse Vision — Архитектура Edge AI, компьютерное зрение и протокол IPC Zero-Port
*Noxfort Systems — A State Of Art Company*

[![Status](https://img.shields.io/badge/Status-Active-brightgreen?style=flat&logo=github)](https://github.com/Noxfort-Systems-Brazil/SVISION)
[![Python](https://img.shields.io/badge/Python-3.12%2B-3776AB?style=flat&logo=python&logoColor=white)](https://python.org/)
[![Tauri](https://img.shields.io/badge/Tauri-2.0%2B-FFC131?style=flat&logo=tauri&logoColor=black)](https://tauri.app/)
[![React](https://img.shields.io/badge/React-19.2-61DAFB?style=flat&logo=react&logoColor=black)](https://react.dev/)
[![Go](https://img.shields.io/badge/Go-1.22%2B-00ADD8?style=flat&logo=go)](https://go.dev/)
[![TensorRT](https://img.shields.io/badge/TensorRT-10.x-76B900?style=flat&logo=nvidia&logoColor=white)](https://developer.nvidia.com/tensorrt)

---

🌐 **Языки / Translations:** **[🇺🇸 English](../en/README.md)** • **[🇧🇷 Português](../pt-br/README.md)** • **[🇪🇸 Español](../es/README.md)** • **[🇫🇷 Français](../fr/README.md)** • **[🇷🇺 Русский](README.md)** • **[🇨🇳 简体中文](../zh/README.md)** • **[📚 Главный портал](../index.md)**

---

</div>

## Добро пожаловать в официальную документацию

Этот каталог содержит техническую документацию на **русском языке** для **SVISION** — суверенной платформы периферийного искусственного интеллекта (*Sovereign Edge AI*) для анализа городского трафика в реальном времени и автономного адаптивного управления светофорными объектами.

## Каталог технических руководств

| Документ | Область | Описание |
|---|---|---|
| 📚 **[Центральный каталог (MOC)](../en/svision_moc.md)** | Главный индекс и граф | Обзор репозитория, структура каталогов и двусторонняя навигация в Obsidian. |
| 🏗️ **[Архитектура системы](../en/architecture_overview.md)** | Базовая архитектура | Трехчастная модель: нативная оболочка Tauri v2 (Rust), ядро Python/CUDA и сетевой шлюз на Go. |
| ⚡ **[GPU пайплайн инференса](../en/gpu_pipeline.md)** | Ускорение TensorRT | Централизованный батчинг на CUDA, переключение моделей YOLO 11 и нейросетевой кроп ROI. |
| 👁️ **[Подсистема компьютерного зрения](../en/vision_subsystem.md)** | Захват и трекинг | Аппаратное декодирование NVDEC, кинематический трекер ByteTrack и расчет скорости. |
| 🔌 **[Архитектура IPC Zero-Port](../en/ipc_architecture.md)** | Межпроцессное взаимодействие | Каналы ОС (`STDIN`/`STDOUT`) с сериализацией JSON-ND без открытых сетевых портов. |
| 🌐 **[Диспетчер Go Synapse](../en/synapse_dispatcher_go.md)** | Сетевой шлюз | Локальный Unix Domain Socket (UDS 0o600) и TCP-мультиплексор для связи с Synapse Core. |
| 🔒 **[Безопасность и LGPD](../en/security_lgpd.md)** | Суверенитет данных | 100% локальная обработка, отсутствие передачи видеокадров и санитарная обработка трейсбеков. |

---

<div align="center">
  <img src="../assets/noxfort-logo.png" alt="Noxfort Systems Logo" width="45" /><br/>
  <b>Noxfort Systems</b> — <i>A State Of Art Company</i><br/>
  <i>Инженерия суверенного периферийного зрения • SVISION v1.2.0</i><br/>
  <small>© 2026 Noxfort Systems. Лицензировано под AGPLv3.</small>
</div>

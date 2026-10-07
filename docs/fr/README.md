<div align="center">

<img src="../assets/svision-logo.png" alt="SVISION Logo" width="120" />

# SVISION — Suite de Documentation Technique
### Synapse Vision — Architecture Edge, Vision par Ordinateur et Framework IPC Zero-Port
*Noxfort Systems — A State Of Art Company*

[![Status](https://img.shields.io/badge/Status-Actif-brightgreen?style=flat&logo=github)](https://github.com/Noxfort-Systems-Brazil/SVISION)
[![Python](https://img.shields.io/badge/Python-3.12%2B-3776AB?style=flat&logo=python&logoColor=white)](https://python.org/)
[![Tauri](https://img.shields.io/badge/Tauri-2.0%2B-FFC131?style=flat&logo=tauri&logoColor=black)](https://tauri.app/)
[![React](https://img.shields.io/badge/React-19.2-61DAFB?style=flat&logo=react&logoColor=black)](https://react.dev/)
[![Go](https://img.shields.io/badge/Go-1.22%2B-00ADD8?style=flat&logo=go)](https://go.dev/)
[![TensorRT](https://img.shields.io/badge/TensorRT-10.x-76B900?style=flat&logo=nvidia&logoColor=white)](https://developer.nvidia.com/tensorrt)

---

🌐 **Traductions / Langues :** **[🇺🇸 English](../en/README.md)** • **[🇧🇷 Português](../pt-br/README.md)** • **[🇪🇸 Español](../es/README.md)** • **[🇫🇷 Français](README.md)** • **[🇷🇺 Русский](../ru/README.md)** • **[🇨🇳 简体中文](../zh/README.md)** • **[📚 Portail de Documentation](../index.md)**

---

</div>

## Bienvenue dans la Documentation Technique Officielle

Ce répertoire rassemble la documentation technique en **Français** pour **SVISION** — une plateforme souveraine d'intelligence artificielle en périphérie (*Sovereign Edge AI*) conçue pour l'analyse du trafic urbain en temps réel et l'orchestration autonome des signaux sans fuite de flux vidéo.

## Répertoire des Guides Techniques

| Document | Thème | Contenu Principal |
|---|---|---|
| 📚 **[Central Master (MOC)](../en/svision_moc.md)** | Index & Graphe de Connaissances | Aperçu du code, hiérarchie architecturale et navigation bidirectionnelle sous Obsidian. |
| 🏗️ **[Architecture Système](../en/architecture_overview.md)** | Architecture Fondamentale | Modèle tripartite : shell desktop Tauri v2 (Rust), moteur cognitif Python/CUDA et passerelle réseau Go. |
| ⚡ **[Pipeline d'Inférence GPU](../en/gpu_pipeline.md)** | Accélération TensorRT | Consommateur de lots CUDA centralisé, boîte de vitesses YOLO 11 et recadrage neuronal par zones d'intérêt. |
| 👁️ **[Sous-système de Vision](../en/vision_subsystem.md)** | Traitement Vidéo & Suivi | Décodage matériel NVDEC, suivi cinématique ByteTrack et calcul de vitesse par homographie. |
| 🔌 **[Architecture IPC Zero-Port](../en/ipc_architecture.md)** | Communication Inter-Processus | Communication par tubes système (`STDIN`/`STDOUT`) en JSON-ND sans aucun port réseau ouvert. |
| 🌐 **[Dispatcher Go Synapse](../en/synapse_dispatcher_go.md)** | Passerelle Réseau | Serveur local Unix Domain Socket (UDS 0o600) et multiplexeur de flux TCP vers le cluster Synapse. |
| 🔒 **[Sécurité et Conformité LGPD](../en/security_lgpd.md)** | Souveraineté Périphérique | Traitement 100% local, aucune sortie de trames d'images brutes et assainissement actif de la mémoire. |

---

<div align="center">
  <img src="../assets/noxfort-logo.png" alt="Noxfort Systems Logo" width="45" /><br/>
  <b>Noxfort Systems</b> — <i>A State Of Art Company</i><br/>
  <i>Ingénierie de Vision Périphérique Souveraine • SVISION v1.2.0</i><br/>
  <small>© 2026 Noxfort Systems. Licencié sous AGPLv3.</small>
</div>

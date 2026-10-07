# 🏛️ SVISION : Architecture Système Tripartite
### Plateforme Souveraine d'IA en Périphérie pour le Trafic Urbain
*Noxfort Systems — A State Of Art Company*

⬅️ [Portail de Documentation](README.md) | ⚡ [Pipeline GPU](../en/gpu_pipeline.md) | 🔌 [IPC Zero-Port](../en/ipc_architecture.md) | 🌐 [Dispatcher Go](../en/synapse_dispatcher_go.md)

---

## 1. Modèle Tripartite en Périphérie Souveraine

**SVISION** répartit ses responsabilités sur trois processus spécialisés et coopératifs au niveau du système d'exploitation :

1. **Shell Desktop (Rust + Tauri v2 + React 19)** : Interface native légère basée sur WebKitGTK consommant ~80% moins de mémoire vive qu'Electron.
2. **Moteur Cognitif IA (Python 3.12 + PyTorch + TensorRT)** : Décodage matériel de flux RTSP via **NVIDIA NVDEC**, découpage dynamique des zones d'intérêt (*Neural Crop & Zoom*) et inférence accélérée avec YOLO 11.
3. **Passerelle Réseau (Dispatcher Go Synapse)** : Isolation de la couche réseau, gestion du socket local Unix Domain Socket (`0o600`) et multiplexage de flux TCP vers le cluster central Synapse.

```text
┌─────────────────────────────────────────────────────────────┐
│                   Architecture Tripartite                   │
│                                                             │
│  ┌──────────────┐     STDIN / STDOUT     ┌──────────────┐   │
│  │ Tauri + React│ ◄════════════════════► │ Python Core  │   │
│  │ (Shell Rust) │  (Tubes Système Zero)  │ (YOLO 11 TRT)│   │
│  └──────────────┘                        └──────┬───────┘   │
│                                                 │ UDS 0o600 │
│                                                 ▼           │
│                                          ┌──────────────┐   │
│                                          │  Dispatcher  │   │
│                                          │  Go Synapse  │   │
│                                          └──────┬───────┘   │
└─────────────────────────────────────────────────┼───────────┘
                                                  │ Flux TCP
                                                  ▼
                                       ┌──────────────────────┐
                                       │ Central Synapse Core │
                                       └──────────────────────┘
```

---

## 2. Principes d'Ingénierie

- **Souveraineté Périphérique** : 100% du traitement vidéo s'exécute sur le matériel local ; aucune image brute n'est transmise au cloud.
- **IPC Zero-Port** : Communication par tubes d'E/S système standard, garantissant zéro port réseau ouvert.
- **Sortie Non Bloquante** : Les interruptions de connectivité sont absorbées par des mémoires tampons circulaires en RAM avec éviction LRU.
- **Conformité RGPD / LGPD** : Masquage et assainissement actif des empreintes mémoire et des piles d'erreurs en production.

---

<div align="center">
  <img src="../assets/noxfort-logo.png" alt="Noxfort Systems Logo" width="45" /><br/>
  <b>Noxfort Systems</b> — <i>A State Of Art Company</i><br/>
  <i>Ingénierie de Vision Périphérique Souveraine • SVISION v1.2.0</i><br/>
  <small>© 2026 Noxfort Systems. Licencié sous AGPLv3.</small>
</div>

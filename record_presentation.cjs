/**
 * SVISION - Automated Presentation Video Generator (Full End-to-End Test Journey)
 * Noxfort Systems (C) 2026
 *
 * Roteiro Completo:
 * 1. Interface Clara (Light Theme) com Status Online do Cluster Edge
 * 2. Visão Geral de Sensores:
 *    - Inspeção da Câmera 01 (Av. Paulista / Al. Campinas) com telemetria viva de 4 abordagens
 *    - Inspeção da Câmera 03 (Marginal Pinheiros / Pte. Estaiada)
 *    - Cadastro de novo sensor via Modal (+ Adicionar Câmera)
 *    - Importação de novos sensores em lote via arquivo CSV
 * 3. Métricas de Máquina (Engine / GPU TensorRT):
 *    - Hardware vivo: 119 FPS, VRAM alocada, CPU e GPU a 56°C
 *    - Gráficos de Alocação de Recursos (ECharts) com curvas contínuas
 *    - Modal de diagnóstico profundo de operação de inferência
 * 4. Malha Synapse (Rede & Go Dispatcher):
 *    - Gráfico de Confiabilidade de Rede (Latência em ms)
 *    - Porteiro de Rede (svision-go) com portas TCP dedicadas e status CONNECTED
 *    - Configuração de IP do Synapse com feedback imediato
 * 5. Configurações & Fechamento:
 *    - Demonstração de alternância de Tema (Claro / Escuro / Claro)
 *    - Retorno à Visão Geral com todo o ecossistema ativo
 */

const { chromium } = require('playwright');
const { execSync, spawn } = require('child_process');
const fs = require('fs');
const path = require('path');
const http = require('http');

const OUTPUT_DIR = path.join(__dirname, 'recordings');
const FINAL_MP4 = path.join(OUTPUT_DIR, 'svision_apresentacao.mp4');
const CSV_PATH = path.join(OUTPUT_DIR, 'cameras_demonstracao.csv');
const APP_URL = 'http://127.0.0.1:5173/?demo=true&theme=light';

function checkServerReady(url, maxRetries = 30) {
  return new Promise((resolve, reject) => {
    let retries = 0;
    const interval = setInterval(() => {
      http.get(url, (res) => {
        clearInterval(interval);
        resolve(true);
      }).on('error', () => {
        retries++;
        if (retries >= maxRetries) {
          clearInterval(interval);
          reject(new Error('Servidor Vite não respondeu a tempo.'));
        }
      });
    }, 500);
  });
}

async function main() {
  if (!fs.existsSync(OUTPUT_DIR)) {
    fs.mkdirSync(OUTPUT_DIR, { recursive: true });
  }

  // Garante que o arquivo CSV de teste exista
  if (!fs.existsSync(CSV_PATH)) {
    fs.writeFileSync(CSV_PATH, 'NomeDaCamera,EnderecoReconhecimento\n"Av. Brigadeiro Faria Lima - Cruzamento JK","rtsp://edge-farialima.internal/stream1"\n"Av. 23 de Maio - Viaduto Santa Generosa","rtsp://edge-23maio.internal/stream1"\n"Av. Engenheiro Luís Carlos Berrini","rtsp://edge-berrini.internal/stream1"\n');
  }

  let viteProcess = null;
  console.log('🔍 Verificando se o servidor Vite está ativo...');
  try {
    await checkServerReady('http://127.0.0.1:5173', 2);
    console.log('✅ Servidor Vite já está em execução na porta 5173.');
  } catch (_) {
    console.log('⚡ Iniciando Vite Dev Server para modo demonstração...');
    viteProcess = spawn(process.execPath, [
      path.join(__dirname, 'node_modules', 'vite', 'bin', 'vite.js'),
      '--port', '5173',
      '--host', '127.0.0.1'
    ], {
      cwd: __dirname,
      stdio: 'pipe'
    });

    await checkServerReady('http://127.0.0.1:5173', 40);
    console.log('✅ Vite Dev Server pronto e respondendo em http://127.0.0.1:5173.');
  }

  console.log('🚀 Iniciando Chromium em modo Full HD (1920x1080 @ 60 FPS)...');
  const chromePath = '/home/gabriel-moraes/.cache/ms-playwright/chromium-1091/chrome-linux/chrome';
  const launchOptions = {
    headless: true,
    args: ['--hide-scrollbars', '--disable-gpu']
  };
  if (fs.existsSync(chromePath)) {
    launchOptions.executablePath = chromePath;
  }

  const browser = await chromium.launch(launchOptions);

  const context = await browser.newContext({
    recordVideo: {
      dir: OUTPUT_DIR,
      size: { width: 1920, height: 1080 }
    },
    viewport: { width: 1920, height: 1080 }
  });

  // Força Tema Claro (Light Mode) corporativo
  await context.addInitScript(() => {
    localStorage.setItem('svision_theme', 'light');
  });

  const page = await context.newPage();

  console.log(`🌐 Acessando SVISION Edge Monitor: ${APP_URL}`);
  await page.goto(APP_URL, { waitUntil: 'networkidle' });

  // 1. Visão Inicial na Interface Clara (5 segundos)
  console.log('☀️ [01] Interface Clara Inicial: Cluster Online e Sensores Urbanos Prontos (5s)...');
  await page.waitForTimeout(5000);

  // 2. Inspeção da Câmera 01 (Av. Paulista)
  console.log('📹 [02] Inspecionando Câmera 01 (Av. Paulista / Al. Campinas)...');
  const cam1 = page.locator('button:has-text("Av. Paulista")');
  if (await cam1.isVisible()) {
    await cam1.click();
  }
  await page.waitForTimeout(5000);

  // 3. Inspeção da Câmera 03 (Marginal Pinheiros)
  console.log('📹 [03] Inspecionando Câmera 03 (Marginal Pinheiros / Pte. Estaiada)...');
  const cam3 = page.locator('button:has-text("Marginal Pinheiros")');
  if (await cam3.isVisible()) {
    await cam3.click();
  }
  await page.waitForTimeout(4000);

  // 4. Cadastro de Nova Câmera via Modal
  console.log('➕ [04] Abrindo Modal de Registro de Novo Sensor de Borda...');
  await page.click('button:has-text("Adicionar Câmera")');
  await page.waitForTimeout(1500);

  console.log('📝 Preenchendo dados do sensor (Av. Rebouças - Corredor Expresso)...');
  const nameInput = page.locator('input[placeholder*="Portão"]');
  await nameInput.fill('Av. Rebouças - Corredor Expresso');
  await page.waitForTimeout(600);

  const addrInput = page.locator('input[placeholder*="live"]');
  await addrInput.fill('rtsp://edge-reboucas.internal/stream1');
  await page.waitForTimeout(600);

  const sensorIdInput = page.locator('input[placeholder*="paulista"]');
  await sensorIdInput.fill('SP_REBOUCAS_BRT');
  await page.waitForTimeout(600);

  const portInput = page.locator('input[placeholder*="9001"]');
  await portInput.fill('9005');
  await page.waitForTimeout(800);

  console.log('💾 Salvando novo sensor no cluster...');
  await page.click('button:has-text("Salvar Sensor")');
  await page.waitForTimeout(4000);

  // 5. Importação em Lote via CSV
  console.log(`📂 [05] Simulando Importação em Lote via CSV (${CSV_PATH})...`);
  const fileInput = page.locator('input[type="file"][accept=".csv"]');
  await fileInput.setInputFiles(CSV_PATH);
  await page.waitForTimeout(4000);

  // 6. Transição para Métricas de Máquina (Engine / GPU)
  console.log('⚙️ [06] Alternando para Métricas de Máquina (Engine & Telemetria GPU)...');
  await page.click('aside nav button:has-text("Máquina")');
  await page.waitForTimeout(6000);

  // 7. Abertura de Modal de Diagnóstico de Operação
  console.log('🔬 [07] Abrindo Modal de Diagnóstico Profundo da Operação de Inferência...');
  const opRow = page.locator('div:has-text("Heuristic Check"), div:has-text("TensorRT INT8 Batch")').first();
  if (await opRow.isVisible()) {
    await opRow.click();
    await page.waitForTimeout(3500);
    // Fecha pressionando Escape
    await page.keyboard.press('Escape');
    await page.waitForTimeout(1500);
  } else {
    // Alternativamente clica no card de FPS
    const fpsCard = page.locator('div:has-text("FPS de Sessões")').first();
    if (await fpsCard.isVisible()) {
      await fpsCard.click();
      await page.waitForTimeout(3500);
      await page.keyboard.press('Escape');
      await page.waitForTimeout(1500);
    }
  }

  // 8. Transição para Malha Synapse (Rede)
  console.log('🌐 [08] Alternando para Malha Synapse (Porteiro svision-go & Portas TCP)...');
  await page.click('aside nav button:has-text("Synapse")');
  await page.waitForTimeout(6000);

  // 9. Configuração de IP da Central Synapse
  console.log('📡 [09] Atualizando IP de Destino da Central Synapse (192.168.1.100)...');
  const ipInput = page.locator('input[placeholder="127.0.0.1"]');
  if (await ipInput.isVisible()) {
    await ipInput.fill('192.168.1.100');
    await page.waitForTimeout(800);
    await page.click('button:has-text("Salvar IP")');
    await page.waitForTimeout(3500);
  }

  // 10. Transição para Configurações & Teste de Tema
  console.log('🎨 [10] Alternando para Configurações (Aparência e Localização)...');
  await page.click('aside button:has-text("Configurações")');
  await page.waitForTimeout(3000);

  console.log('🌙 Alternando para Modo Escuro (Dark Theme)...');
  await page.click('button:has-text("Modo Escuro")');
  await page.waitForTimeout(2500);

  console.log('☀️ Retornando para Modo Claro (Light Theme)...');
  await page.click('button:has-text("Modo Claro")');
  await page.waitForTimeout(2500);

  // 11. Retorno à Visão Geral de Sensores
  console.log('🔄 [11] Retornando à Visão Geral de Sensores com Cluster em Operação...');
  await page.click('aside nav button:has-text("Sensores")');
  await page.waitForTimeout(5000);

  const video = page.video();
  await page.close();
  await context.close();
  await browser.close();

  if (viteProcess) {
    viteProcess.kill('SIGTERM');
  }

  if (video) {
    const rawWebmPath = await video.path();
    console.log(`\n🎬 Vídeo bruto capturado: ${rawWebmPath}`);
    console.log('⚙️ Codificando vídeo final em MP4 (H.264 @ 60 FPS, Alta Qualidade, 1080p)...');

    execSync(`ffmpeg -y -i "${rawWebmPath}" -c:v libx264 -pix_fmt yuv420p -r 60 -crf 18 "${FINAL_MP4}"`, {
      stdio: 'inherit'
    });

    console.log(`\n🎉 VÍDEO DO SVISION GERADO COM SUCESSO!`);
    console.log(`📁 Arquivo final: ${FINAL_MP4}\n`);
  }
}

main().catch((err) => {
  console.error('❌ Erro durante a geração do vídeo:', err);
  process.exit(1);
});

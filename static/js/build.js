/**
 * VivaCRM Frontend Build Script
 * Bu script, Webpack veya Rollup olmadan temel asset birleştirme işlemlerini yapar
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// Yapılandırma
const config = {
  // Giriş noktaları
  entries: {
    // Alpine.js bileşenleri
    alpine: [
      './static/js/alpine/helpers/formatters.js',
      './static/js/alpine/components/modal.js',
      './static/js/alpine/components/card.js', 
      './static/js/alpine/stores/theme.js',
      './static/js/alpine/index.js',
    ],
    
    // HTMX yardımcıları
    htmx: [
      './static/js/htmx/helpers.js',
    ],
    
    // Ana uygulama
    app: [
      './static/js/app-modern.js',
    ],
  },
  
  // Çıktı dizini
  output: {
    path: './static/js/dist',
    // Çıktı dosyaları
    files: {
      'alpine-bundle.js': ['alpine'],
      'htmx-helpers.js': ['htmx'],
      'app.js': ['app'],
    },
  },
  
  // Minifikasyon
  minify: {
    enabled: true,
    command: 'terser', // Başka bir komut da kullanılabilir
    options: '--compress --mangle --module', 
  },
};

// Çalışma dizinini kontrol et
if (!fs.existsSync('./static')) {
  console.error('static dizini bulunamadı! Script proje kök dizininden çalıştırılmalıdır.');
  process.exit(1);
}

// Çıktı dizinini oluştur
if (!fs.existsSync(config.output.path)) {
  fs.mkdirSync(config.output.path, { recursive: true });
  console.log(`Çıktı dizini oluşturuldu: ${config.output.path}`);
}

// Her bir çıktı dosyası için
Object.entries(config.output.files).forEach(([outputFile, entryGroups]) => {
  // Dosya içeriklerini topla
  let mergedContent = '';
  
  // Her bir giriş grubunu işle
  entryGroups.forEach(entryGroup => {
    const entryFiles = config.entries[entryGroup];
    
    // Her bir giriş dosyasını oku ve birleştir
    entryFiles.forEach(entryFile => {
      if (!fs.existsSync(entryFile)) {
        console.warn(`Uyarı: Dosya bulunamadı: ${entryFile}, atlanıyor...`);
        return;
      }
      
      const content = fs.readFileSync(entryFile, 'utf8');
      mergedContent += `\n/* ${path.basename(entryFile)} */\n${content}\n`;
    });
  });
  
  // Çıktı dosya yolunu oluştur
  const outputPath = path.join(config.output.path, outputFile);
  
  // Normal çıktıyı yaz
  fs.writeFileSync(outputPath, mergedContent);
  console.log(`Çıktı dosyası oluşturuldu: ${outputPath}`);
  
  // Minifiye edilmiş çıktıyı yaz (eğer etkinse)
  if (config.minify.enabled) {
    const minOutputPath = outputPath.replace(/\.js$/, '.min.js');
    
    try {
      // Minifikasyon komutu çalıştır
      execSync(`${config.minify.command} ${outputPath} ${config.minify.options} -o ${minOutputPath}`);
      console.log(`Minifiye edilmiş çıktı dosyası oluşturuldu: ${minOutputPath}`);
    } catch (error) {
      console.error('Minifikasyon hatası:', error.message);
      console.error('Terser kurulu değilse: npm install -g terser');
    }
  }
});

console.log('Build işlemi tamamlandı!');

// CSS derleme (PostCSS/Tailwind)
console.log('CSS derleme başlatılıyor...');
try {
  // Tarayıcı öneki ve minifikasyon ile CSS derle
  execSync('npx postcss ./static/css/main.css -o ./static/css/dist/main.css');
  console.log('CSS derleme tamamlandı: ./static/css/dist/main.css');
  
  // Minifiye CSS oluştur
  execSync('npx postcss ./static/css/main.css -o ./static/css/dist/main.min.css --env production');
  console.log('Minifiye CSS derleme tamamlandı: ./static/css/dist/main.min.css');
} catch (error) {
  console.error('CSS derleme hatası:', error.message);
  console.error('PostCSS veya Tailwind kurulu değilse: npm install -g postcss-cli tailwindcss autoprefixer cssnano');
}

// CSS ve JS dosyalarının boyutunu rapor et
function formatBytes(bytes) {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

console.log('\nOluşturulan dosya boyutları:');
console.log('----------------------------');

// JS dosyaları boyutları
Object.keys(config.output.files).forEach(outputFile => {
  const filePath = path.join(config.output.path, outputFile);
  const minFilePath = filePath.replace(/\.js$/, '.min.js');
  
  if (fs.existsSync(filePath)) {
    const stats = fs.statSync(filePath);
    console.log(`${outputFile}: ${formatBytes(stats.size)}`);
  }
  
  if (fs.existsSync(minFilePath)) {
    const minStats = fs.statSync(minFilePath);
    console.log(`${outputFile.replace(/\.js$/, '.min.js')}: ${formatBytes(minStats.size)}`);
  }
});

// CSS dosyaları boyutları
const cssPath = './static/css/dist/main.css';
const minCssPath = './static/css/dist/main.min.css';

if (fs.existsSync(cssPath)) {
  const cssStats = fs.statSync(cssPath);
  console.log(`main.css: ${formatBytes(cssStats.size)}`);
}

if (fs.existsSync(minCssPath)) {
  const minCssStats = fs.statSync(minCssPath);
  console.log(`main.min.css: ${formatBytes(minCssStats.size)}`);
}
// frontend/static/js/dashboard.js

// Global Variables
let currentProducts = [];
let filteredProducts = [];
let currentScripts = [];
let scriptPersonas = [];
let voicePersonas = [];

// Initialize Dashboard
document.addEventListener('DOMContentLoaded', function () {
    initializeDashboard();
});

async function initializeDashboard() {
    console.log('🚀 Initializing AI Live Commerce Dashboard...');

    // Setup navigation
    setupNavigation();

    // Load initial data
    await Promise.all([
        loadDashboardStats(),
        loadProducts(),
        loadPersonas()
    ]);

    console.log('✅ Dashboard initialized successfully');

    window.addEventListener('error', function (e) {
        if (e.message && e.message.includes('filter is not a function')) {
            console.warn('🔧 Auto-fixing filter error...');
            if (typeof currentScripts !== 'undefined') {
                currentScripts = [];
            }
            return false; // Prevent error popup
        }
    });

    // 🔧 Console commands สำหรับ debugging (ใช้ใน browser console)
    console.log(`
        🔧 Dashboard.js Fixed - Debug Commands Available:
        window.debugScripts.checkCurrentScripts() - ตรวจสอบ currentScripts
        window.debugScripts.forceArrayReset() - รีเซ็ต currentScripts
        window.debugScripts.testAPI(productId) - ทดสอบ API
        window.debugScripts.forceReload() - โหลด scripts ใหม่
    `);
}

function setupNavigation() {
    const navItems = document.querySelectorAll('.nav-item');
    const contentSections = document.querySelectorAll('.content-section');

    navItems.forEach(item => {
        item.addEventListener('click', function (e) {
            e.preventDefault();

            const targetSection = this.getAttribute('data-section');

            // Update active nav item
            navItems.forEach(nav => nav.classList.remove('active'));
            this.classList.add('active');

            // Update active content section
            contentSections.forEach(section => section.classList.remove('active'));
            document.getElementById(targetSection + '-section').classList.add('active');

            // Load section-specific data
            loadSectionData(targetSection);
        });
    });
}

async function loadSectionData(section) {
    switch (section) {
        case 'overview':
            await loadDashboardStats();
            break;
        case 'products':
            await loadProducts();
            break;
        case 'scripts':
            await loadProductsForScriptsFilter();
            break;
    }
}

// Load personas
async function loadPersonas() {
    try {
        const [scriptResponse, voiceResponse] = await Promise.all([
            fetch('/api/v1/dashboard/personas/script'),
            fetch('/api/v1/dashboard/personas/voice')
        ]);

        if (scriptResponse.ok) {
            scriptPersonas = await scriptResponse.json();
        }
        if (voiceResponse.ok) {
            voicePersonas = await voiceResponse.json();
        }

    } catch (error) {
        console.error('Error loading personas:', error);
    }
}

// AI Script Generation
function showAIScriptGenerationModal(productId) {
    const product = currentProducts.find(p => p.id === productId);

    if (!scriptPersonas.length) {
        showAlert('No script personas available. Please create script personas first.', 'error');
        return;
    }

    const modal = `
        <div class="modal-overlay" onclick="closeModal()">
            <div class="modal-content" onclick="event.stopPropagation()">
                <div class="modal-header">
                    <h3>🤖 Generate AI Scripts for ${escapeHtml(product.name)}</h3>
                    <button class="modal-close" onclick="closeModal()">&times;</button>
                </div>
                <div class="modal-body">
                    <div class="form-group">
                        <label class="form-label">Script Persona:</label>
                        <select class="form-control" id="script-persona-select">
                            ${scriptPersonas.map(persona =>
        `<option value="${persona.id}">${escapeHtml(persona.name)} - ${escapeHtml(persona.description || persona.speaking_style || '')}</option>`
    ).join('')}
                        </select>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Mood/Emotion:</label>
                        <select class="form-control" id="script-mood-select">
                            <option value="auto">Auto (Let AI decide)</option>
                            <option value="excited">😄 Excited - ตื่นเต้น กระตือรือร้น</option>
                            <option value="professional">👔 Professional - มืออาชีพ เป็นทางการ</option>
                            <option value="friendly">😊 Friendly - เป็นกันเอง อบอุ่น</option>
                            <option value="confident">💪 Confident - มั่นใจ เชื่อมั่น</option>
                            <option value="energetic">⚡ Energetic - มีพลัง เร่าร้อน</option>
                            <option value="calm">😌 Calm - สงบ ใจเย็น</option>
                            <option value="urgent">⏰ Urgent - เร่งด่วน จำกัดเวลา</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Number of Scripts:</label>
                        <select class="form-control" id="script-count-select">
                            <option value="3">3 Scripts (Recommended)</option>
                            <option value="5">5 Scripts</option>
                            <option value="1">1 Script</option>
                        </select>
                    </div>
                    <div class="alert alert-info">
                        <strong>🎭 Emotional TTS:</strong> Scripts will include emotional markup tags for TTS to express the right mood and feeling.
                    </div>
                </div>
                <div class="modal-actions">
                    <button class="btn btn-secondary" onclick="closeModal()">Cancel</button>
                    <button class="btn btn-primary" onclick="executeAIScriptGeneration(${productId})">
                        <i class="fas fa-robot"></i> Generate Scripts
                    </button>
                </div>
            </div>
        </div>
    `;

    showModal(modal);
}

async function executeAIScriptGeneration(productId) {
    const personaId = document.getElementById('script-persona-select').value;
    const mood = document.getElementById('script-mood-select').value;
    const count = parseInt(document.getElementById('script-count-select').value);

    if (!personaId) {
        showAlert('Please select a script persona', 'error');
        return;
    }

    try {
        showAlert('กำลังสร้าง AI scripts พร้อม emotional markup...', 'info');
        closeModal();

        const response = await fetch('/api/v1/dashboard/scripts/generate-ai', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                product_id: parseInt(productId),
                persona_id: parseInt(personaId),
                mood: mood,
                count: count
            })
        });

        if (response.ok) {
            const result = await response.json();
            showAlert(`สร้าง ${result.scripts.length} AI scripts พร้อม emotional markup สำเร็จ!`, 'success');

            // อัพเดทข้อมูล scripts ใน memory
            currentScripts = result.scripts;

            // Switch to scripts section และแสดงผล
            switchToScriptsSection(productId);

            // รีโหลด products stats ด้วย
            await loadDashboardStats();
        } else {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to generate scripts');
        }

    } catch (error) {
        console.error('Error generating AI scripts:', error);
        showAlert('Failed to generate AI scripts: ' + error.message, 'error');
    }
}

async function switchToScriptsSection(productId) {
    // Update navigation
    document.querySelectorAll('.nav-item').forEach(nav => nav.classList.remove('active'));
    document.querySelector('[data-section="scripts"]').classList.add('active');

    // Update content sections
    document.querySelectorAll('.content-section').forEach(section => section.classList.remove('active'));
    document.getElementById('scripts-section').classList.add('active');

    // Set product filter และโหลด scripts ใหม่จาก API
    await loadProductsForScriptsFilter(); // Ensure filter is populated
    document.getElementById('scripts-product-filter').value = productId;

    // รีโหลด scripts จาก API เพื่อให้แน่ใจว่าได้ข้อมูลล่าสุด
    await loadScripts();
}

// Scripts Management
async function loadProductsForScriptsFilter() {
    try {
        console.log('📄 Loading products for scripts filter...');

        const response = await fetch('/api/v1/dashboard/products');

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const data = await response.json();
        const products = data.products || [];
        const select = document.getElementById('scripts-product-filter');

        if (!select) {
            console.error('❌ scripts-product-filter element not found');
            return;
        }

        const currentValue = select.value;

        // ✨ เพิ่ม "ALL" option
        select.innerHTML = `
            <option value="">Select Product</option>
            <option value="all">🌟 ALL Products</option>
            ${products.map(product =>
            `<option value="${product.id}">${escapeHtml(product.name)} (${escapeHtml(product.sku)})</option>`
        ).join('')}
        `;

        // Restore previous selection if it still exists
        if (currentValue === "all" || products.some(p => p.id == currentValue)) {
            select.value = currentValue;
        }

        console.log(`✅ Loaded ${products.length} products for filter with ALL option`);
    } catch (error) {
        console.error('❌ Error loading products for filter:', error);
        const select = document.getElementById('scripts-product-filter');
        if (select) {
            select.innerHTML = '<option value="">Error loading products</option>';
        }
        showAlert('ไม่สามารถโหลดรายการสินค้าได้: ' + error.message, 'error');
    }
}

async function loadScripts() {
    const productId = document.getElementById('scripts-product-filter').value;
    const contentDiv = document.getElementById('scripts-content');

    if (!productId) {
        contentDiv.innerHTML = '<div class="loading"><i class="fas fa-info-circle"></i><p>Select a product to view scripts...</p></div>';
        return;
    }

    try {
        console.log('🔍 Loading scripts for product:', productId);

        let allScripts = [];

        if (productId === "all") {
            // ✨ สำหรับ ALL - ดึงจากทุกสินค้า
            console.log('📋 Loading scripts from ALL products...');

            // ดึงรายการสินค้าทั้งหมดก่อน
            const productsResponse = await fetch('/api/v1/dashboard/products');
            if (!productsResponse.ok) {
                throw new Error('Failed to fetch products');
            }
            const productsData = await productsResponse.json();
            const products = productsData.products || [];

            // ดึง scripts จากแต่ละสินค้า
            const scriptPromises = products.map(async (product) => {
                try {
                    const response = await fetch(`/api/v1/dashboard/products/${product.id}/scripts`);
                    if (response.ok) {
                        const data = await response.json();
                        const scripts = data.scripts || [];
                        // เพิ่ม product info ให้แต่ละ script
                        return scripts.map(script => ({
                            ...script,
                            product_name: product.name,
                            product_sku: product.sku
                        }));
                    }
                    return [];
                } catch (error) {
                    console.warn(`Failed to load scripts for product ${product.id}:`, error);
                    return [];
                }
            });

            // รอให้ดึงครบทุกสินค้า
            const scriptArrays = await Promise.all(scriptPromises);
            allScripts = scriptArrays.flat(); // รวมทุก array เป็น array เดียว

            console.log(`✅ Loaded ${allScripts.length} scripts from ${products.length} products`);

        } else {
            // ดึงจากสินค้าเดียว (เหมือนเดิม)
            const response = await fetch(`/api/v1/dashboard/products/${productId}/scripts`);
            if (!response.ok) {
                throw new Error(`Failed to fetch scripts. Status: ${response.status}`);
            }

            const data = await response.json();
            allScripts = data.scripts || [];
        }

        // ตรวจสอบและจัดเก็บ scripts
        if (Array.isArray(allScripts)) {
            currentScripts = allScripts;
        } else {
            console.warn('⚠️ Scripts data is not an array');
            currentScripts = [];
        }

        console.log('✅ Scripts loaded:', currentScripts.length, 'items');
        displayScripts(productId === "all" ? "all" : productId);

    } catch (error) {
        console.error('❌ Error loading scripts:', error);
        currentScripts = [];
        const contentDiv = document.getElementById('scripts-content');
        contentDiv.innerHTML = `
            <div class="alert alert-error" style="margin: 20px;">
                <h4>⚠️ ไม่สามารถโหลด scripts ได้</h4>
                <p>Error: ${error.message}</p>
                <button class="btn btn-primary" onclick="loadScripts()">🔄 ลองใหม่</button>
            </div>
        `;
        showAlert('ไม่สามารถโหลด scripts ได้: ' + error.message, 'error');
    }
}


function displayScripts(productId) {
    const contentDiv = document.getElementById('scripts-content');

    // 🔧 แก้ไขจุดนี้ - ตรวจสอบว่า currentScripts เป็น array ก่อนใช้ filter
    if (!Array.isArray(currentScripts)) {
        console.warn('⚠️ currentScripts is not an array, resetting to empty array');
        currentScripts = [];
    }

    // 🆕 จัดการการแสดงผลสำหรับ "ALL"
    let product = null;
    let displayTitle = "";
    let scriptsToShow = currentScripts;

    if (productId === "all") {
        displayTitle = "📋 All Scripts from All Products";
        // Group scripts by product for better display
        const productGroups = {};
        scriptsToShow.forEach(script => {
            const prodName = script.product_name || `Product ID ${script.product_id}`;
            if (!productGroups[prodName]) {
                productGroups[prodName] = [];
            }
            productGroups[prodName].push(script);
        });
    } else {
        product = currentProducts.find(p => p.id == productId);
        displayTitle = `📋 Scripts for ${product ? escapeHtml(product.name) : 'Selected Product'}`;
    }

    const scriptsWithoutMP3 = scriptsToShow.filter(s => s && !s.has_mp3);
    const scriptsWithMP3 = scriptsToShow.filter(s => s && s.has_mp3);

    contentDiv.innerHTML = `
        <div class="section-header" style="border-bottom: 1px solid var(--border-color);">
            <h3>${displayTitle}</h3>
            <div class="section-actions">
                ${productId !== "all" ? `
                    <button class="btn btn-primary btn-sm" onclick="showCreateManualScriptModal(${productId})">
                        <i class="fas fa-plus"></i> Manual Script
                    </button>
                    <button class="btn btn-success btn-sm" onclick="showAIScriptGenerationModal(${productId})">
                        <i class="fas fa-robot"></i> AI Scripts
                    </button>
                ` : ''}
                ${scriptsWithoutMP3.length > 0 ? `
                    <button class="btn btn-warning btn-sm" onclick="showBulkMP3GenerationModal('${productId}')">
                        <i class="fas fa-music"></i> Bulk MP3 (${scriptsWithoutMP3.length})
                    </button>
                ` : ''}
            </div>
        </div>
        <div class="scripts-list" style="padding: 20px;">
            ${scriptsToShow.length > 0 ? `
                <div class="scripts-summary" style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <strong>📊 Summary:</strong> 
                            ${scriptsToShow.length} scripts total | 
                            <span style="color: var(--success-color);">✅ ${scriptsWithMP3.length} with MP3</span> | 
                            <span style="color: var(--warning-color);">📝 ${scriptsWithoutMP3.length} pending MP3</span>
                        </div>
                        ${scriptsWithoutMP3.length > 1 && productId !== "all" ? `
                            <button class="btn btn-sm btn-success" onclick="showBulkMP3GenerationModal('${productId}')">
                                <i class="fas fa-music"></i> Generate All MP3s
                            </button>
                        ` : ''}
                    </div>
                </div>
                ${scriptsToShow.map(script => createScriptCard(script)).join('')}
            ` : `
                <div class="text-center" style="padding: 40px;">
                    <i class="fas fa-file-alt" style="font-size: 3rem; color: var(--text-secondary); margin-bottom: 15px;"></i>
                    <h3>No scripts found</h3>
                    ${productId !== "all" ? `
                        <p>Generate some AI scripts to get started!</p>
                        <button class="btn btn-primary mt-10" onclick="showAIScriptGenerationModal(${productId})">
                            <i class="fas fa-robot"></i> Generate AI Scripts
                        </button>
                    ` : '<p>No scripts available from any products.</p>'}
                </div>
            `}
        </div>
    `;
}

function createScriptCard(script) {
    const displayContent = formatEmotionalMarkup(script.content);
    const borderColor = script.has_mp3 ? 'var(--success-color)' : 'var(--primary-color)';

    return `
        <div class="script-card" style="background: white; border-radius: 8px; margin-bottom: 20px; padding: 20px; border-left: 4px solid ${borderColor}; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
            <div class="script-header" style="margin-bottom: 15px;">
                <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 10px;">
                    <h4 style="margin: 0; flex: 1;">${escapeHtml(script.title)}</h4>
                    <div style="text-align: right;">
                        ${script.has_mp3 ?
            '<span class="status-badge status-completed" style="background: #d4edda; color: #155724;"><i class="fas fa-music"></i> MP3 Ready</span>' :
            '<span class="status-badge status-processing" style="background: #fff3cd; color: #856404;"><i class="fas fa-clock"></i> Script Only</span>'
        }
                    </div>
                </div>
                <div class="d-flex gap-10 align-center" style="flex-wrap: wrap;">
                    <span class="status-badge status-info">${script.script_type}</span>
                    ${script.persona_name ? `<span class="status-badge status-active">👤 ${escapeHtml(script.persona_name)}</span>` : ''}
                    ${script.target_emotion ? `<span class="status-badge" style="background: #e3f2fd; color: #1976d2;">🎭 ${script.target_emotion}</span>` : ''}
                    ${script.duration_estimate ? `<span class="text-secondary">⏱️ ~${script.duration_estimate}s</span>` : ''}
                    ${script.word_count ? `<span class="text-secondary">📝 ${script.word_count} words</span>` : ''}
                    ${script.product_name ? `<span class="status-badge" style="background: #f3e5f5; color: #7b1fa2;">🏷️ ${escapeHtml(script.product_name)}</span>` : ''}
                </div>
            </div>
            <div class="script-content" style="background: #f8f9fa; padding: 15px; border-radius: 6px; margin-bottom: 15px; max-height: 300px; overflow-y: auto; line-height: 1.6;">
                ${displayContent}
            </div>
            <div class="script-actions" style="display: flex; gap: 8px; flex-wrap: wrap;">
                ${script.has_mp3 ? `
                    <!-- ✅ มี MP3 แล้ว - แสดงปุ่ม Play และ Delete MP3 -->
                    <button class="btn btn-success btn-sm" onclick="playMP3(${script.id})" title="Play MP3 audio">
                        <i class="fas fa-play"></i> Play Audio
                    </button>
                    <button class="btn btn-danger btn-sm" onclick="deleteMP3(${script.id})" title="Delete MP3 and unlock script for editing">
                        <i class="fas fa-trash"></i> Delete MP3
                    </button>
                ` : `
                    <!-- ❌ ยังไม่มี MP3 - แสดงปุ่ม Edit และ Create MP3 -->
                    <button class="btn btn-primary btn-sm" onclick="editScript(${script.id})" title="Edit script content">
                        <i class="fas fa-edit"></i> Edit Script
                    </button>
                    <button class="btn btn-success btn-sm" onclick="generateMP3ForScript(${script.id})" title="Generate MP3 from this script">
                        <i class="fas fa-music"></i> Create MP3
                    </button>
                `}
                <button class="btn btn-danger btn-sm" onclick="deleteScript(${script.id}, '${escapeHtml(script.title)}')" title="Delete script and all MP3 files">
                    <i class="fas fa-trash"></i> Delete Script
                </button>
            </div>
            ${script.has_mp3 ? `
                <div class="mp3-info" style="background: #e8f5e8; padding: 10px; border-radius: 6px; margin-top: 15px; font-size: 0.9rem;">
                    <strong>🎵 MP3 Information:</strong><br>
                    <span class="text-secondary">
                        🎧 Ready for live streaming | 
                        🔒 Script is locked (delete MP3 to edit) |
                        ⏱️ Est. duration: ${script.duration_estimate || 'Unknown'}s
                    </span>
                </div>
            ` : ''}
        </div>
    `;
}

async function downloadMP3(scriptId) {
    try {
        const response = await fetch(`/api/v1/dashboard/scripts/${scriptId}`);
        if (!response.ok) throw new Error('Script not found');
        const script = await response.json();

        if (!script.has_mp3) {
            showAlert('This script does not have an MP3 file yet.', 'warning');
            return;
        }

        const downloadUrl = `/static/audio/script_${scriptId}.mp3`;
        const link = document.createElement('a');
        link.href = downloadUrl;
        link.download = `${script.title.replace(/[^a-z0-9]/gi, '_').toLowerCase()}.mp3`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        showAlert('🎵 MP3 download started!', 'success');

    } catch (error) {
        console.error('Error downloading MP3:', error);
        showAlert('Error downloading MP3 file: ' + error.message, 'error');
    }
}

function formatEmotionalMarkup(content) {
    let formatted = escapeHtml(content);
    const emotionStyles = {
        'excited': 'color: #ff6b35; font-weight: bold;', 'happy': 'color: #4ecdc4; font-weight: bold;',
        'professional': 'color: #2c5aa0; font-weight: 500;', 'confident': 'color: #8e44ad; font-weight: bold;',
        'energetic': 'color: #e74c3c; font-weight: bold;', 'calm': 'color: #27ae60; font-style: italic;',
        'warm': 'color: #f39c12; font-weight: 500;', 'friendly': 'color: #16a085; font-weight: 500;',
        'trustworthy': 'color: #34495e; font-weight: 500;', 'urgent': 'color: #e74c3c; font-weight: bold; text-decoration: underline;'
    };

    Object.keys(emotionStyles).forEach(emotion => {
        const regex = new RegExp(`\\{${emotion}\\}(.*?)\\{\\/${emotion}\\}`, 'g');
        formatted = formatted.replace(regex, `<span style="${emotionStyles[emotion]}" title="Emotion: ${emotion}">$1</span>`);
    });

    return formatted.replace(/\\n/g, '<br>');
}

// ... (The rest of the JS code remains the same)
// ...
// ... [Continue with the rest of your JavaScript functions like viewScriptDetails, editScript, deleteScript, etc.]
// ...

async function viewScriptDetails(scriptId) {
    try {
        const response = await fetch(`/api/v1/dashboard/scripts/${scriptId}`);
        if (!response.ok) {
            throw new Error('Script not found');
        }

        const script = await response.json();

        const modal = `
            <div class="modal-overlay" onclick="closeModal()">
                <div class="modal-content" onclick="event.stopPropagation()">
                    <div class="modal-header">
                        <h3>📝 Script Details: ${escapeHtml(script.title)}</h3>
                        <button class="modal-close" onclick="closeModal()">&times;</button>
                    </div>
                    <div class="modal-body">
                        <div class="form-group">
                            <strong>📊 Script Information:</strong>
                            <div style="background: #f8f9fa; padding: 15px; border-radius: 6px; margin-top: 10px;">
                                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 15px;">
                                    <div>
                                        <strong>Type:</strong> ${script.script_type}<br>
                                        <strong>Language:</strong> ${script.language || 'th'}<br>
                                        <strong>Status:</strong> ${script.status}
                                    </div>
                                    <div>
                                        <strong>Words:</strong> ${script.word_count || 0}<br>
                                        <strong>Duration:</strong> ~${script.duration_estimate || 0}s<br>
                                        <strong>Has MP3:</strong> ${script.has_mp3 ? '✅ Yes' : '❌ No'}
                                    </div>
                                </div>
                                ${script.persona_name ? `<strong>Persona:</strong> ${escapeHtml(script.persona_name)}<br>` : ''}
                                ${script.target_emotion ? `<strong>Emotion:</strong> ${script.target_emotion}<br>` : ''}
                                ${script.call_to_action ? `<strong>Call to Action:</strong> ${escapeHtml(script.call_to_action)}<br>` : ''}
                            </div>
                        </div>
                        <div class="form-group">
                            <strong>📄 Script Content:</strong>
                            <div style="background: #f8f9fa; padding: 15px; border-radius: 6px; margin-top: 10px; max-height: 300px; overflow-y: auto; line-height: 1.6;">
                                ${formatEmotionalMarkup(script.content)}
                            </div>
                        </div>
                        ${script.has_mp3 ? `
                            <div class="form-group">
                                <strong>🎵 MP3 Status:</strong>
                                <div style="background: #e8f5e8; padding: 15px; border-radius: 6px; margin-top: 10px;">
                                    ✅ MP3 file is ready for use<br>
                                    🔒 Script editing is locked<br>
                                    📁 File available for download and playback
                                </div>
                            </div>
                        ` : ''}
                    </div>
                    <div class="modal-actions">
                        <button class="btn btn-secondary" onclick="closeModal()">Close</button>
                        ${script.can_edit ? `
                            <button class="btn btn-primary" onclick="closeModal(); editScript(${script.id})">
                                <i class="fas fa-edit"></i> Edit Script
                            </button>
                        ` : ''}
                        ${!script.has_mp3 ? `
                            <button class="btn btn-success" onclick="closeModal(); generateMP3ForScript(${script.id})">
                                <i class="fas fa-music"></i> Generate MP3
                            </button>
                        ` : `
                            <button class="btn btn-success" onclick="closeModal(); playMP3(${script.id})">
                                <i class="fas fa-play"></i> Play MP3
                            </button>
                        `}
                    </div>
                </div>
            </div>
        `;
        showModal(modal);

    } catch (error) {
        console.error('Error loading script details:', error);
        showAlert('Failed to load script details: ' + error.message, 'error');
    }
}

async function editScript(scriptId) {
    try {
        // 🔥 ดึงข้อมูลใหม่จาก server เสมอ
        console.log('📝 Loading fresh script data for editing:', scriptId);

        const response = await fetch(`/api/v1/dashboard/scripts/${scriptId}`);
        if (!response.ok) {
            throw new Error('Failed to load script data');
        }

        const script = await response.json();
        console.log('📄 Fresh script data:', script);

        // 🔥 ตรวจสอบให้เข้มงวด
        if (script.has_mp3 === true) {
            showAlert('❌ ไม่สามารถแก้ไขสคริปต์ได้ เนื่องจากมี MP3 ผูกอยู่', 'warning');
            console.warn('🚫 Edit blocked - Script has MP3:', {
                scriptId: scriptId,
                has_mp3: script.has_mp3,
                can_edit: script.can_edit
            });
            return;
        }

        if (script.can_edit === false) {
            showAlert('❌ สคริปต์นี้ถูกล็อค ไม่สามารถแก้ไขได้', 'warning');
            console.warn('🚫 Edit blocked - Script locked:', script);
            return;
        }

        console.log('✅ Script is editable - showing modal');

        // แสดง modal สำหรับแก้ไข
        const modal = `
            <div class="modal-overlay" onclick="closeModal()">
                <div class="modal-content" onclick="event.stopPropagation()">
                    <div class="modal-header">
                        <h3>✏️ แก้ไขสคริปต์: ${escapeHtml(script.title)}</h3>
                        <button class="modal-close" onclick="closeModal()">&times;</button>
                    </div>
                    <div class="modal-body">
                        <div class="form-group">
                            <label>ชื่อสคริปต์:</label>
                            <input type="text" class="form-control" id="edit-script-title" value="${escapeHtml(script.title)}">
                        </div>
                        <div class="form-group">
                            <label>เนื้อหาสคริปต์:</label>
                            <textarea class="form-control" id="edit-script-content" rows="10">${escapeHtml(script.content)}</textarea>
                        </div>
                        <div class="form-group">
                            <label>อารมณ์:</label>
                            <select class="form-control" id="edit-script-emotion">
                                <option value="professional" ${script.target_emotion === 'professional' ? 'selected' : ''}>🎯 มืออาชีพ</option>
                                <option value="friendly" ${script.target_emotion === 'friendly' ? 'selected' : ''}>😊 เป็นมิตร</option>
                                <option value="excited" ${script.target_emotion === 'excited' ? 'selected' : ''}>🔥 ตื่นเต้น</option>
                                <option value="confident" ${script.target_emotion === 'confident' ? 'selected' : ''}>💪 มั่นใจ</option>
                                <option value="energetic" ${script.target_emotion === 'energetic' ? 'selected' : ''}>⚡ กระตือรือร้น</option>
                                <option value="calm" ${script.target_emotion === 'calm' ? 'selected' : ''}>😌 สงบ</option>
                                <option value="urgent" ${script.target_emotion === 'urgent' ? 'selected' : ''}>⏰ เร่งด่วน</option>
                            </select>
                        </div>
                    </div>
                    <div class="modal-actions">
                        <button class="btn btn-secondary" onclick="closeModal()">ยกเลิก</button>
                        <button class="btn btn-primary" onclick="confirmUpdateScript(${scriptId})">
                            <i class="fas fa-save"></i> บันทึก
                        </button>
                    </div>
                </div>
            </div>
        `;
        showModal(modal);

    } catch (error) {
        console.error('❌ Error loading script for editing:', error);
        showAlert('ไม่สามารถโหลดข้อมูลสคริปต์ได้: ' + error.message, 'error');
    }
}

async function confirmUpdateScript(scriptId) {
    if (!confirm('คุณต้องการบันทึกการแก้ไขสคริปต์นี้หรือไม่?')) return;

    const updateData = {
        title: document.getElementById('edit-script-title').value,
        content: document.getElementById('edit-script-content').value,
        target_emotion: document.getElementById('edit-script-emotion').value
    };

    try {
        const response = await fetch(`/api/v1/dashboard/scripts/${scriptId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(updateData)
        });

        if (response.ok) {
            showAlert('บันทึกการแก้ไขสคริปต์สำเร็จ!', 'success');
            closeModal();
            await loadScripts(); // Reload scripts
        } else {
            throw new Error('Failed to update script');
        }
    } catch (error) {
        showAlert('ไม่สามารถบันทึกการแก้ไขได้: ' + error.message, 'error');
    }
}

async function deleteScript(scriptId, title) {
    if (!confirm(`คุณต้องการลบสคริปต์ "${title}" หรือไม่?\n\nการลบจะส่งผลให้ MP3 ที่เกี่ยวข้องถูกลบด้วย`)) {
        return;
    }

    try {
        const response = await fetch(`/api/v1/dashboard/scripts/${scriptId}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            showAlert(`ลบสคริปต์ "${title}" สำเร็จ!`, 'success');
            await loadScripts(); // Reload scripts
            await loadDashboardStats(); // Update stats
        } else {
            throw new Error('Failed to delete script');
        }
    } catch (error) {
        showAlert('ไม่สามารถลบสคริปต์ได้: ' + error.message, 'error');
    }
}

async function generateMP3ForScript(scriptId) {
    const script = currentScripts.find(s => s.id === scriptId);
    if (!script) {
        showAlert('Script not found', 'error');
        return;
    }

    if (!voicePersonas.length) {
        showAlert('No voice personas available. Please create voice personas first.', 'error');
        return;
    }

    try {
        // 🆕 ดึงข้อมูล TTS Providers ที่มีอยู่
        const providersResponse = await fetch('/api/v1/dashboard/tts/providers');
        const providersData = await providersResponse.json();

        console.log('🎤 Available TTS Providers:', providersData);

        const modal = `
            <div class="modal-overlay" onclick="closeModal()">
                <div class="modal-content" onclick="event.stopPropagation()">
                    <div class="modal-header">
                        <h3>🎵 Enhanced MP3 Generation for: ${escapeHtml(script.title)}</h3>
                        <button class="modal-close" onclick="closeModal()">&times;</button>
                    </div>
                    <div class="modal-body">
                        <!-- 🆕 TTS Provider Selection -->
                        <div class="form-group">
                            <label class="form-label">🎤 TTS Provider:</label>
                            <select class="form-control" id="tts-provider-select" onchange="updateProviderVoices()">
                                ${generateProviderOptions(providersData.providers)}
                            </select>
                            <small class="text-secondary" id="provider-description">Select TTS provider for audio generation.</small>
                        </div>

                        <!-- Voice Selection (filtered by provider) -->
                        <div class="form-group">
                            <label class="form-label">🗣️ Voice Persona:</label>
                            <select class="form-control" id="voice-persona-select" onchange="updateEmotionOptions()">
                                <!-- Options will be populated by updateProviderVoices() -->
                            </select>
                            <small class="text-secondary">Enhanced voices support emotional expressions.</small>
                        </div>

                        <!-- Emotion Selection -->
                        <div class="form-group">
                            <label class="form-label">🎭 Emotion & Mood:</label>
                            <select class="form-control" id="emotion-select">
                                <option value="professional">🎯 Professional</option>
                                <option value="friendly">😊 Friendly</option>
                                <option value="excited">🔥 Excited</option>
                                <option value="confident">💪 Confident</option>
                                <option value="energetic">⚡ Energetic</option>
                                <option value="calm">😌 Calm</option>
                                <option value="cheerful">🎉 Cheerful</option>
                                <option value="gentle">🌸 Gentle</option>
                                <option value="serious">🎖️ Serious</option>
                                <option value="urgent">⏰ Urgent</option>
                            </select>
                            <small class="text-secondary" id="emotion-description">Select the emotional tone.</small>
                        </div>

                        <!-- Emotion Intensity -->
                        <div class="form-group">
                            <label class="form-label">🌟 Emotion Intensity:</label>
                            <input type="range" class="form-control" id="emotion-intensity" min="0.5" max="2.0" step="0.1" value="1.2">
                            <div style="display: flex; justify-content: space-between; font-size: 0.8rem; color: var(--text-secondary);">
                                <span>Subtle</span><span id="intensity-value">1.2</span><span>Intense</span>
                            </div>
                        </div>

                        <!-- Audio Quality -->
                        <div class="form-group">
                            <label class="form-label">🔊 Audio Quality:</label>
                            <select class="form-control" id="mp3-quality-select">
                                <option value="enhanced">✨ Enhanced (Best)</option>
                                <option value="high">📊 High Quality</option>
                                <option value="medium" selected>🎵 Medium Quality (Recommended)</option>
                                <option value="low">📻 Low Quality (Fast)</option>
                            </select>
                        </div>

                        <!-- Script Preview -->
                        <div class="alert alert-info">
                            <strong>📄 Script Preview:</strong><br>
                            <div style="max-height: 150px; overflow-y: auto; background: #f8f9fa; padding: 10px; border-radius: 4px; margin-top: 10px;">
                                ${formatEmotionalMarkup(script.content)}
                            </div>
                        </div>
                    </div>
                    <div class="modal-actions">
                        <button class="btn btn-secondary" onclick="closeModal()">Cancel</button>
                        <button class="btn btn-success" onclick="confirmEnhancedMP3Generation(${scriptId})">
                            <i class="fas fa-magic"></i> Generate Enhanced MP3
                        </button>
                    </div>
                </div>
            </div>
        `;
        showModal(modal);

        // Initialize modal functionality
        setupEnhancedTTSEventListeners();
        updateProviderVoices(); // Load initial voices

    } catch (error) {
        console.error('Error loading TTS providers:', error);
        showAlert('Failed to load TTS provider info. Using basic mode.', 'warning');
        generateMP3ForScriptFallback(scriptId); // Fallback to simple modal
    }
}

function generateMP3ForScriptFallback(scriptId) {
    const script = currentScripts.find(s => s.id === scriptId);

    const modal = `
        <div class="modal-overlay" onclick="closeModal()">
            <div class="modal-content" onclick="event.stopPropagation()">
                <div class="modal-header">
                    <h3>🎵 MP3 Generation for: ${escapeHtml(script.title)}</h3>
                    <button class="modal-close" onclick="closeModal()">&times;</button>
                </div>
                <div class="modal-body">
                    <div class="form-group">
                        <label class="form-label">Voice Persona:</label>
                        <select class="form-control" id="voice-persona-select">
                            ${voicePersonas.map(persona => `<option value="${persona.id}">${escapeHtml(persona.name)}</option>`).join('')}
                        </select>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Quality:</label>
                        <select class="form-control" id="mp3-quality-select">
                            <option value="medium" selected>Medium (Recommended)</option>
                            <option value="high">High</option>
                            <option value="low">Low (Fast)</option>
                        </select>
                    </div>
                </div>
                <div class="modal-actions">
                    <button class="btn btn-secondary" onclick="closeModal()">Cancel</button>
                    <button class="btn btn-success" onclick="confirmBasicMP3Generation(${scriptId})">
                        <i class="fas fa-music"></i> Generate MP3
                    </button>
                </div>
            </div>
        </div>
    `;
    showModal(modal);
}

async function confirmBasicMP3Generation(scriptId) {
    const voicePersonaId = document.getElementById('voice-persona-select').value;
    const quality = document.getElementById('mp3-quality-select').value;

    try {
        closeModal();
        showAlert('🎵 Generating MP3...', 'info');

        const response = await fetch('/api/v1/dashboard/mp3/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                script_ids: [scriptId],
                voice_persona_id: parseInt(voicePersonaId),
                quality: quality
            })
        });

        if (response.ok) {
            showAlert('✅ MP3 generation started!', 'success');
            pollMP3Generation(scriptId);
        } else {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to start MP3 generation');
        }

    } catch (error) {
        console.error('Error generating MP3:', error);
        showAlert('Failed to generate MP3: ' + error.message, 'error');
    }
}

function generateProviderOptions(providers) {
    if (!providers) {
        return '<option value="edge">🎭 Microsoft Edge TTS (Default)</option>';
    }

    let options = '';

    // Sort providers by quality/preference
    const providerOrder = ['edge', 'azure', 'elevenlabs', 'google', 'basic'];

    providerOrder.forEach(providerKey => {
        const provider = providers[providerKey];
        if (provider && provider.available) {
            const providerInfo = getProviderInfo(providerKey, provider);
            options += `<option value="${providerKey}" data-voices='${JSON.stringify(provider.voices || {})}'>${providerInfo.icon} ${providerInfo.name} ${providerInfo.badge}</option>`;
        }
    });

    return options || '<option value="edge">🎭 Microsoft Edge TTS (Default)</option>';
}

function getProviderInfo(key, provider) {
    const providerMap = {
        'edge': {
            name: 'Microsoft Edge TTS',
            icon: '🎭',
            badge: '(Best Quality)'
        },
        'azure': {
            name: 'Azure Speech Services',
            icon: '🏢',
            badge: '(Enterprise)'
        },
        'elevenlabs': {
            name: 'ElevenLabs AI',
            icon: '🤖',
            badge: '(Premium AI)'
        },
        'google': {
            name: 'Google Text-to-Speech',
            icon: '🔍',
            badge: '(Standard)'
        },
        'basic': {
            name: 'Basic TTS',
            icon: '📢',
            badge: '(Free)'
        }
    };

    return providerMap[key] || {
        name: key.charAt(0).toUpperCase() + key.slice(1),
        icon: '🎤',
        badge: ''
    };
}

function updateProviderVoices() {
    const providerSelect = document.getElementById('tts-provider-select');
    const voiceSelect = document.getElementById('voice-persona-select');
    const providerDesc = document.getElementById('provider-description');

    if (!providerSelect || !voiceSelect) return;

    const selectedProvider = providerSelect.value;
    const selectedOption = providerSelect.options[providerSelect.selectedIndex];

    // Update provider description
    if (providerDesc) {
        const descriptions = {
            'edge': '🎭 Microsoft Edge TTS - High quality, natural voices with emotional support',
            'azure': '🏢 Azure Speech Services - Enterprise-grade TTS with advanced features',
            'elevenlabs': '🤖 ElevenLabs AI - Premium AI-powered voices with realistic expression',
            'google': '🔍 Google TTS - Standard quality, reliable performance',
            'basic': '📢 Basic TTS - Simple text-to-speech, free tier'
        };
        providerDesc.textContent = descriptions[selectedProvider] || 'Select TTS provider for audio generation.';
    }

    // Filter voice personas by selected provider
    const filteredVoices = voicePersonas.filter(persona =>
        !persona.tts_provider || persona.tts_provider === selectedProvider
    );

    // Update voice options
    voiceSelect.innerHTML = filteredVoices.map(persona => {
        const providerLabel = getProviderInfo(persona.tts_provider || selectedProvider, {}).icon;
        const premiumLabel = persona.is_premium ? ' 💎' : '';

        return `<option value="${persona.id}" data-provider="${persona.tts_provider || selectedProvider}" data-emotions='${JSON.stringify(persona.emotional_range || [])}'>
                    ${providerLabel} ${escapeHtml(persona.name)}${premiumLabel}
                </option>`;
    }).join('');

    // Update emotions for first voice
    updateEmotionOptions();
}



function setupEnhancedTTSEventListeners() {
    const intensitySlider = document.getElementById('emotion-intensity');
    const intensityValue = document.getElementById('intensity-value');

    if (intensitySlider && intensityValue) {
        intensitySlider.addEventListener('input', function () {
            intensityValue.textContent = this.value;
        });
    }
    updateEmotionOptions();
}

async function updateEmotionOptions() {
    const voiceSelect = document.getElementById('voice-persona-select');
    const emotionSelect = document.getElementById('emotion-select');
    if (!voiceSelect || !emotionSelect) return;

    const selectedOption = voiceSelect.options[voiceSelect.selectedIndex];
    const supportedEmotions = JSON.parse(selectedOption.getAttribute('data-emotions') || '[]');

    Array.from(emotionSelect.options).forEach(option => {
        const isSupported = supportedEmotions.includes(option.value);
        option.style.background = isSupported ? '#e8f5e8' : '';
        option.style.fontWeight = isSupported ? 'bold' : '';
    });
}

async function confirmEnhancedMP3Generation(scriptId) {
    if (!scriptId) {
        showAlert('Script ID is missing.', 'error');
        return;
    }

    const ttsProvider = document.getElementById('tts-provider-select').value;
    const voicePersonaId = document.getElementById('voice-persona-select').value;
    const emotion = document.getElementById('emotion-select').value;
    const quality = document.getElementById('mp3-quality-select').value;
    const intensity = parseFloat(document.getElementById('emotion-intensity').value);

    try {
        closeModal();
        showAlert(`🎵 Generating Enhanced MP3 with ${ttsProvider.toUpperCase()} TTS...`, 'info');

        const response = await fetch('/api/v1/dashboard/mp3/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                script_ids: [scriptId],
                voice_persona_id: parseInt(voicePersonaId),
                tts_provider: ttsProvider, // 🆕 เพิ่ม provider selection
                quality: quality,
                emotion: emotion,
                intensity: intensity
            })
        });

        if (response.ok) {
            const result = await response.json();
            showAlert(`✅ Enhanced MP3 generation started with ${ttsProvider.toUpperCase()}!`, 'success');
            pollMP3Generation(scriptId);
        } else {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to start Enhanced MP3 generation');
        }

    } catch (error) {
        console.error('Error generating Enhanced MP3:', error);
        showAlert('Failed to generate Enhanced MP3: ' + error.message, 'error');
    }
}

async function pollMP3Generation(scriptId, attempts = 0) {
    const maxAttempts = 30; // 30-second timeout

    if (attempts >= maxAttempts) {
        showAlert('⏱️ MP3 generation is taking longer than expected. Please refresh to check status.', 'warning');
        return;
    }

    try {
        const response = await fetch(`/api/v1/dashboard/scripts/${scriptId}`);
        if (response.ok) {
            const script = await response.json();
            if (script.has_mp3) {
                showAlert('🎉 MP3 generation completed successfully!', 'success');
                await loadScripts();
                await loadDashboardStats();
                return;
            }
        }
        setTimeout(() => pollMP3Generation(scriptId, attempts + 1), 1000);
    } catch (error) {
        console.error('Error polling MP3 status:', error);
        setTimeout(() => pollMP3Generation(scriptId, attempts + 1), 1000);
    }
}

async function playMP3(scriptId) {
    try {
        console.log('🎵 Playing MP3 for script:', scriptId);

        // ✨ ดึงข้อมูล MP3 file จาก API ก่อน
        const mp3InfoResponse = await fetch(`/api/v1/dashboard/mp3/status/${scriptId}`);
        if (!mp3InfoResponse.ok) {
            throw new Error('Failed to get MP3 file information');
        }

        const mp3Data = await mp3InfoResponse.json();
        console.log('📁 MP3 Data:', mp3Data);

        // ตรวจสอบว่ามี MP3 files หรือไม่
        if (!mp3Data.mp3_files || mp3Data.mp3_files.length === 0) {
            showAlert('🚫 This script does not have an MP3 file yet.', 'warning');
            return;
        }

        // ใช้ไฟล์แรกที่มีสถานะ completed
        const completedMP3 = mp3Data.mp3_files.find(file => file.status === 'completed');
        if (!completedMP3) {
            showAlert('🚫 No completed MP3 file found for this script.', 'warning');
            return;
        }

        // ✨ ใช้ชื่อไฟล์จริงจาก database
        const audioUrl = `/static/audio/${completedMP3.filename}`;
        console.log('🎧 Audio URL:', audioUrl);

        // ตรวจสอบว่ามี audio player อยู่แล้วหรือไม่
        let existingPlayer = document.getElementById('mp3-player');
        if (existingPlayer) {
            existingPlayer.remove();
        }

        // สร้าง audio player ใหม่
        const audioPlayer = document.createElement('audio');
        audioPlayer.id = 'mp3-player';
        audioPlayer.controls = true;
        audioPlayer.autoplay = true;
        audioPlayer.style.cssText = `
            position: fixed;
            bottom: 20px;
            right: 20px;
            z-index: 1000;
            background: white;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            border: 2px solid var(--primary-color);
            max-width: 300px;
        `;

        // เพิ่ม source
        const source = document.createElement('source');
        source.src = audioUrl;
        source.type = 'audio/mpeg';
        audioPlayer.appendChild(source);

        // เพิ่ม event listeners
        audioPlayer.addEventListener('loadstart', () => {
            showAlert('🎵 Loading audio...', 'info');
        });

        audioPlayer.addEventListener('canplay', () => {
            showAlert(`🎧 Playing: ${mp3Data.script_title}`, 'success');
        });

        audioPlayer.addEventListener('error', (e) => {
            console.error('Audio playback error:', e);
            showAlert(`❌ Failed to play audio. File: ${completedMP3.filename}`, 'error');
            audioPlayer.remove();
        });

        audioPlayer.addEventListener('ended', () => {
            showAlert('✅ Playback completed!', 'success');
            setTimeout(() => {
                if (audioPlayer.parentNode) {
                    audioPlayer.remove();
                }
            }, 3000);
        });

        // เพิ่ม title display
        const titleDiv = document.createElement('div');
        titleDiv.style.cssText = `
            background: var(--primary-color);
            color: white;
            padding: 5px 10px;
            font-size: 12px;
            border-radius: 6px 6px 0 0;
            font-weight: bold;
            text-align: center;
        `;
        titleDiv.textContent = mp3Data.script_title || `Script ${scriptId}`;

        // เพิ่ม close button
        const closeButton = document.createElement('button');
        closeButton.innerHTML = '❌';
        closeButton.style.cssText = `
            position: absolute;
            top: -10px;
            right: -10px;
            background: var(--error-color);
            color: white;
            border: none;
            border-radius: 50%;
            width: 25px;
            height: 25px;
            cursor: pointer;
            font-size: 12px;
        `;
        closeButton.onclick = () => {
            audioPlayer.pause();
            wrapper.remove();
            showAlert('🔇 Audio stopped', 'info');
        };

        // สร้าง wrapper
        const wrapper = document.createElement('div');
        wrapper.style.cssText = `
            position: fixed;
            bottom: 20px;
            right: 20px;
            z-index: 1000;
            background: white;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            border: 2px solid var(--primary-color);
        `;

        wrapper.appendChild(titleDiv);
        wrapper.appendChild(audioPlayer);
        wrapper.appendChild(closeButton);

        // เพิ่มลงใน DOM
        document.body.appendChild(wrapper);

        console.log('🎧 Audio player created for:', audioUrl);

    } catch (error) {
        console.error('Error playing MP3:', error);
        showAlert('❌ Error playing audio: ' + error.message, 'error');
    }
}

async function deleteMP3(scriptId) {
    if (!confirm('คุณต้องการลบ MP3 ไฟล์นี้หรือไม่?')) return;

    try {
        const response = await fetch(`/api/v1/dashboard/scripts/${scriptId}/mp3`, {
            method: 'DELETE'
        });

        if (response.ok) {
            showAlert('✅ MP3 deleted! สคริปต์ถูกปลดล็อคแล้ว', 'success');

            // 🔥 แก้ไขจุดนี้ - รีเฟรชข้อมูลทันที
            console.log('🔄 Force refreshing scripts after MP3 deletion...');

            // อัปเดตใน memory ก่อน
            const scriptIndex = currentScripts.findIndex(s => s.id === scriptId);
            if (scriptIndex !== -1) {
                currentScripts[scriptIndex].has_mp3 = false;
                currentScripts[scriptIndex].can_edit = true;
            }

            // 🔥 บังคับโหลดใหม่ทันที
            setTimeout(async () => {
                await loadScripts();
                console.log('✅ Scripts force reloaded');
            }, 500);

        } else {
            throw new Error('Failed to delete MP3');
        }
    } catch (error) {
        console.error('❌ Error deleting MP3:', error);
        showAlert('Failed to delete MP3: ' + error.message, 'error');
    }
}

async function showBulkMP3GenerationModal(productId) {
    let productScripts;

    if (productId === "all") {
        // ดึงสคริปต์ทั้งหมดที่ยังไม่มี MP3
        productScripts = currentScripts.filter(s => s && !s.has_mp3);
    } else {
        // ดึงสคริปต์ของสินค้าที่เลือก
        productScripts = currentScripts.filter(s => s.product_id == productId && !s.has_mp3);
    }

    if (!productScripts.length) {
        showAlert('No scripts available for MP3 generation.', 'warning');
        return;
    }
    if (!voicePersonas.length) {
        showAlert('No voice personas available.', 'error');
        return;
    }

    const modalTitle = productId === "all" ?
        `🎵 Bulk MP3 Generation - All Products (${productScripts.length} scripts)` :
        `🎵 Bulk MP3 Generation`;

    const modal = `
        <div class="modal-overlay" onclick="closeModal()">
            <div class="modal-content" onclick="event.stopPropagation()">
                <div class="modal-header">
                    <h3>${modalTitle}</h3>
                    <button class="modal-close" onclick="closeModal()">&times;</button>
                </div>
                <div class="modal-body">
                    <div class="form-group">
                        <label class="form-label">Select Scripts:</label>
                        <div style="max-height: 200px; overflow-y: auto; border: 1px solid var(--border-color); padding: 10px; border-radius: 6px;">
                            ${productScripts.map(script => `
                                <label style="display: block; margin-bottom: 8px;">
                                    <input type="checkbox" id="script-${script.id}" value="${script.id}" checked style="margin-right: 8px;">
                                    ${escapeHtml(script.title)}
                                    ${productId === "all" && script.product_name ? `<span style="color: #666;"> (${escapeHtml(script.product_name)})</span>` : ''}
                                </label>
                            `).join('')}
                        </div>
                        <small class="text-secondary">
                            <button type="button" class="btn btn-sm btn-secondary" onclick="toggleAllScripts(true)" style="margin-top: 5px;">Select All</button>
                            <button type="button" class="btn btn-sm btn-secondary" onclick="toggleAllScripts(false)" style="margin-top: 5px;">Deselect All</button>
                        </small>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Voice Persona:</label>
                        <select class="form-control" id="bulk-voice-persona-select">
                            ${voicePersonas.map(persona => `<option value="${persona.id}">${escapeHtml(persona.name)}</option>`).join('')}
                        </select>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Quality:</label>
                        <select class="form-control" id="bulk-mp3-quality-select">
                            <option value="medium">Medium (Recommended)</option>
                            <option value="high">High</option>
                            <option value="low">Low (Fast)</option>
                        </select>
                    </div>
                </div>
                <div class="modal-actions">
                    <button class="btn btn-secondary" onclick="closeModal()">Cancel</button>
                    <button class="btn btn-success" onclick="confirmBulkMP3Generation()">
                        <i class="fas fa-music"></i> Generate All
                    </button>
                </div>
            </div>
        </div>
    `;
    showModal(modal);
}

function toggleAllScripts(checked) {
    document.querySelectorAll('input[type="checkbox"][id^="script-"]').forEach(cb => cb.checked = checked);
}

async function confirmBulkMP3Generation() {
    const selectedScriptIds = Array.from(document.querySelectorAll('input[type="checkbox"][id^="script-"]:checked')).map(cb => parseInt(cb.value));
    const voicePersonaId = document.getElementById('bulk-voice-persona-select').value;
    const quality = document.getElementById('bulk-mp3-quality-select').value;

    if (!selectedScriptIds.length || !voicePersonaId) {
        showAlert('Please select scripts and a voice persona.', 'error');
        return;
    }

    try {
        showAlert(`🎵 Starting bulk MP3 generation for ${selectedScriptIds.length} scripts...`, 'info');
        closeModal();

        const response = await fetch('/api/v1/dashboard/mp3/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                script_ids: selectedScriptIds,
                voice_persona_id: parseInt(voicePersonaId),
                quality: quality
            })
        });

        if (response.ok) {
            showAlert(`✅ Bulk MP3 generation started!`, 'success');
            pollBulkMP3Generation(selectedScriptIds);
        } else {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to start bulk MP3 generation');
        }

    } catch (error) {
        console.error('Error generating bulk MP3:', error);
        showAlert('Failed to generate bulk MP3: ' + error.message, 'error');
    }
}

async function pollBulkMP3Generation(scriptIds, attempts = 0) {
    if (attempts >= 60) {
        showAlert('⏱️ Bulk MP3 generation is taking a while. Please refresh to check status.', 'warning');
        return;
    }
    try {
        const responses = await Promise.all(scriptIds.map(id => fetch(`/api/v1/dashboard/scripts/${id}`)));
        const scripts = await Promise.all(responses.map(res => res.json()));
        const completedCount = scripts.filter(s => s.has_mp3).length;

        if (completedCount === scriptIds.length) {
            showAlert(`🎉 Bulk MP3 generation complete! ${completedCount} files created.`, 'success');
            await loadScripts();
            await loadDashboardStats();
            return;
        } else if (completedCount > 0) {
            showAlert(`⏳ Processing... ${completedCount}/${scriptIds.length} completed`, 'info');
        }
        setTimeout(() => pollBulkMP3Generation(scriptIds, attempts + 1), 2000);
    } catch (error) {
        console.error('Error polling bulk MP3 status:', error);
        setTimeout(() => pollBulkMP3Generation(scriptIds, attempts + 1), 2000);
    }
}

function showCreateManualScriptModal(productId) {
    showAlert('Manual script creation coming soon!', 'info');
}

// Dashboard Stats
async function loadDashboardStats() {
    try {
        const response = await fetch('/api/v1/dashboard/stats');
        const data = await response.json();
        document.getElementById('total-products').textContent = data.products.total;
        document.getElementById('active-products').textContent = data.products.active;
        document.getElementById('total-scripts').textContent = data.content.scripts;
        document.getElementById('total-mp3s').textContent = data.content.mp3_files;
    } catch (error) {
        console.error('Error loading dashboard stats:', error);
        showAlert('Failed to load dashboard statistics', 'error');
    }
}

// Products Management
async function loadProducts() {
    const category = document.getElementById('category-filter')?.value || '';
    const status = document.getElementById('status-filter')?.value || '';
    try {
        showProductsLoading();
        const params = new URLSearchParams({ category, status }).toString();
        const response = await fetch(`/api/v1/dashboard/products?${params}`);
        if (!response.ok) throw new Error(`HTTP Error: ${response.status}`);
        const data = await response.json();
        currentProducts = data.products || [];
        filteredProducts = [...currentProducts];
        displayProducts();
    } catch (error) {
        console.error('Error loading products:', error);
        showAlert('Failed to load products: ' + error.message, 'error');
        showProductsError();
    }
}

function showProductsLoading() {
    document.getElementById('products-grid').innerHTML = `<div class="loading" style="grid-column: 1/-1;"><i class="fas fa-spinner"></i><p>Loading products...</p></div>`;
}

function showProductsError() {
    document.getElementById('products-grid').innerHTML = `<div class="text-center" style="grid-column: 1/-1; padding: 40px;"><i class="fas fa-exclamation-triangle" style="font-size: 3rem; color: var(--error-color);"></i><h3>Failed to load products</h3><button class="btn btn-primary mt-10" onclick="loadProducts()">Retry</button></div>`;
}

function displayProducts() {
    const grid = document.getElementById('products-grid');
    if (!filteredProducts.length) {
        grid.innerHTML = `<div class="text-center" style="grid-column: 1/-1; padding: 40px;"><i class="fas fa-box" style="font-size: 3rem;"></i><h3>No products found</h3><button class="btn btn-primary mt-10" onclick="showCreateProductModal()">Add Product</button></div>`;
        return;
    }
    grid.innerHTML = filteredProducts.map(p => createProductCard(p)).join('');
}

function createProductCard(product) {
    return `
        <div class="product-card">
            <div class="product-header">
                <div class="product-name">${escapeHtml(product.name)}</div>
                <div class="product-sku">SKU: ${escapeHtml(product.sku)}</div>
            </div>
            <div class="product-info">
                <div class="product-price">
                    ${product.is_on_sale ?
            `<span style="text-decoration: line-through; color: #999;">฿${(product.original_price || 0).toLocaleString()}</span> ฿${(product.sale_price || 0).toLocaleString()}` :
            `฿${(product.price || 0).toLocaleString()}`
        }
                </div>
                <div class="product-stats">
                    <span><i class="fas fa-file-alt"></i> ${product.total_scripts || 0}</span>
                    <span><i class="fas fa-music"></i> ${product.total_mp3s || 0}</span>
                    <span><i class="fas fa-video"></i> ${product.total_videos || 0}</span>
                </div>
            </div>
            <div class="product-actions">
                <button class="btn btn-primary btn-sm" onclick="viewProduct(${product.id})"><i class="fas fa-eye"></i> View</button>
                <button class="btn btn-success btn-sm" onclick="showAIScriptGenerationModal(${product.id})"><i class="fas fa-robot"></i> AI Scripts</button>
                <button class="btn btn-secondary btn-sm" onclick="editProduct(${product.id})"><i class="fas fa-edit"></i> Edit</button>
                <button class="btn btn-danger btn-sm" onclick="deleteProduct(${product.id}, '${escapeHtml(product.name)}')"><i class="fas fa-trash"></i> Delete</button>
            </div>
        </div>
    `;
}

function searchProducts() {
    const searchTerm = document.getElementById('search-products').value.toLowerCase();
    filteredProducts = currentProducts.filter(p =>
        p.name.toLowerCase().includes(searchTerm) ||
        p.sku.toLowerCase().includes(searchTerm)
    );
    displayProducts();
}

// Product CRUD
function showCreateProductModal() {
    const modal = `
        <div class="modal-overlay" onclick="closeModal()">
            <div class="modal-content" onclick="event.stopPropagation()">
                <div class="modal-header"><h3>Add New Product</h3><button class="modal-close" onclick="closeModal()">&times;</button></div>
                <div class="modal-body">
                    <form id="product-form">
                        <div class="form-group"><label>SKU *</label><input type="text" class="form-control" id="product-sku" required></div>
                        <div class="form-group"><label>Name *</label><input type="text" class="form-control" id="product-name" required></div>
                        <div class="form-group"><label>Description</label><textarea class="form-control" id="product-description" rows="3"></textarea></div>
                        <div class="form-group"><label>Price *</label><input type="number" class="form-control" id="product-price" required></div>
                        <div class="form-group"><label>Category</label><select class="form-control" id="product-category"><option value="">Select</option><option value="electronics">Electronics</option><option value="fashion">Fashion</option></select></div>
                    </form>
                </div>
                <div class="modal-actions">
                    <button class="btn btn-secondary" onclick="closeModal()">Cancel</button>
                    <button class="btn btn-primary" onclick="saveProduct()">Save</button>
                </div>
            </div>
        </div>
    `;
    showModal(modal);
}

async function saveProduct() {
    const productData = {
        sku: document.getElementById('product-sku').value,
        name: document.getElementById('product-name').value,
        description: document.getElementById('product-description').value,
        price: parseFloat(document.getElementById('product-price').value),
        category: document.getElementById('product-category').value,
    };
    if (!productData.sku || !productData.name || !productData.price) {
        showAlert('Please fill in all required fields.', 'error');
        return;
    }
    try {
        const response = await fetch('/api/v1/dashboard/products', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(productData)
        });
        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || 'Failed to create product');
        }
        closeModal();
        showAlert('Product created successfully!', 'success');
        await loadProducts();
    } catch (error) {
        showAlert('Failed to create product: ' + error.message, 'error');
    }
}

async function viewProduct(id) {
    try {
        const response = await fetch(`/api/v1/dashboard/products/${id}`);
        if (!response.ok) throw new Error('Product not found');
        const product = await response.json();
        const modal = `
            <div class="modal-overlay" onclick="closeModal()">
                <div class="modal-content" onclick="event.stopPropagation()">
                    <div class="modal-header"><h3>Product Details</h3><button class="modal-close" onclick="closeModal()">&times;</button></div>
                    <div class="modal-body">
                        <strong>SKU:</strong> ${escapeHtml(product.sku)}<br>
                        <strong>Name:</strong> ${escapeHtml(product.name)}<br>
                        <strong>Price:</strong> ฿${(product.price || 0).toLocaleString()}<br>
                        <strong>Description:</strong> ${escapeHtml(product.description || 'N/A')}
                    </div>
                    <div class="modal-actions">
                        <button class="btn btn-secondary" onclick="closeModal()">Close</button>
                        <button class="btn btn-primary" onclick="closeModal(); editProduct(${product.id})">Edit</button>
                    </div>
                </div>
            </div>
        `;
        showModal(modal);
    } catch (error) {
        showAlert('Failed to load product details.', 'error');
    }
}

async function editProduct(id) {
    try {
        const response = await fetch(`/api/v1/dashboard/products/${id}`);
        if (!response.ok) throw new Error('Product not found');
        const product = await response.json();
        showEditProductModal(product);
    } catch (error) {
        showAlert('Failed to load product for editing.', 'error');
    }
}

function showEditProductModal(product) {
    const modal = `
        <div class="modal-overlay" onclick="closeModal()">
            <div class="modal-content" onclick="event.stopPropagation()">
                <div class="modal-header"><h3>Edit Product</h3><button class="modal-close" onclick="closeModal()">&times;</button></div>
                <div class="modal-body">
                    <input type="hidden" id="edit-product-id" value="${product.id}">
                    <div class="form-group"><label>SKU *</label><input type="text" class="form-control" id="edit-product-sku" value="${escapeHtml(product.sku)}" required></div>
                    <div class="form-group"><label>Name *</label><input type="text" class="form-control" id="edit-product-name" value="${escapeHtml(product.name)}" required></div>
                    <div class="form-group"><label>Description</label><textarea class="form-control" id="edit-product-description">${escapeHtml(product.description || '')}</textarea></div>
                    <div class="form-group"><label>Price *</label><input type="number" class="form-control" id="edit-product-price" value="${product.price}" required></div>
                </div>
                <div class="modal-actions">
                    <button class="btn btn-secondary" onclick="closeModal()">Cancel</button>
                    <button class="btn btn-primary" onclick="updateProduct()">Update</button>
                </div>
            </div>
        </div>
    `;
    showModal(modal);
}

async function updateProduct() {
    const id = document.getElementById('edit-product-id').value;
    const productData = {
        sku: document.getElementById('edit-product-sku').value,
        name: document.getElementById('edit-product-name').value,
        description: document.getElementById('edit-product-description').value,
        price: parseFloat(document.getElementById('edit-product-price').value),
    };
    try {
        const response = await fetch(`/api/v1/dashboard/products/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(productData)
        });
        if (!response.ok) throw new Error('Failed to update product');
        closeModal();
        showAlert('Product updated successfully!', 'success');
        await loadProducts();
    } catch (error) {
        showAlert('Failed to update product: ' + error.message, 'error');
    }
}

async function deleteProduct(id, name) {
    if (!confirm(`Are you sure you want to delete "${name}"? This will delete all related content.`)) return;
    try {
        const response = await fetch(`/api/v1/dashboard/products/${id}`, { method: 'DELETE' });
        if (!response.ok) throw new Error('Failed to delete product');
        showAlert('Product deleted successfully!', 'success');
        await loadProducts();
        await loadDashboardStats();
    } catch (error) {
        showAlert('Failed to delete product: ' + error.message, 'error');
    }
}

// Utility Functions
function showModal(content) {
    document.getElementById('modal-container').innerHTML = content;
}

function closeModal() {
    document.getElementById('modal-container').innerHTML = '';
}

function showAlert(message, type = 'info') {
    const alertContainer = document.getElementById('alert-container');
    const alertClass = type === 'error' ? 'alert-error' : type === 'success' ? 'alert-success' : 'alert-info';
    const alert = document.createElement('div');
    alert.className = `alert ${alertClass}`;
    alert.innerHTML = `${message}<button style="float: right; background: none; border: none; font-size: 1.2rem; cursor: pointer;" onclick="this.parentElement.remove()">&times;</button>`;
    alertContainer.appendChild(alert);
    setTimeout(() => alert.remove(), 5000);
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

async function refreshDashboard() {
    await initializeDashboard();
    showAlert('Dashboard refreshed successfully!', 'success');
}

window.debugScripts = {
    checkCurrentScripts: function () {
        console.log('🔍 Debug currentScripts:');
        console.log('  Type:', typeof currentScripts);
        console.log('  Is Array:', Array.isArray(currentScripts));
        console.log('  Length:', currentScripts?.length);
        console.log('  Content:', currentScripts);
        return currentScripts;
    },

    forceArrayReset: function () {
        console.log('🔧 Force resetting currentScripts to empty array');
        currentScripts = [];
        console.log('✅ Reset complete');
        return currentScripts;
    },

    testAPI: async function (productId = 1) {
        try {
            console.log(`🧪 Testing API for product ${productId}`);
            const response = await fetch(`/api/v1/dashboard/products/${productId}/scripts`);
            const data = await response.json();
            console.log('📊 API Response:', data);
            console.log('📊 Scripts type:', typeof data.scripts);
            console.log('📊 Is array:', Array.isArray(data.scripts));
            return data;
        } catch (error) {
            console.error('❌ API Test failed:', error);
            return null;
        }
    },

    forceReload: function () {
        console.log('🔄 Force reloading scripts...');
        const productId = document.getElementById('scripts-product-filter')?.value;
        if (productId) {
            loadScripts();
        } else {
            console.warn('⚠️ No product selected');
        }
    }
};
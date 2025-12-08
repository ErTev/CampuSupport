
// Helper: decode JWT payload (simple base64) to extract role as a fallback
function decodeJwt(token) {
    try {
        const parts = token.split('.');
        if (parts.length !== 3) return null;
        const payload = JSON.parse(atob(parts[1].replace(/-/g, '+').replace(/_/g, '/')));
        return payload;
    } catch (e) {
        console.error('JWT decode error', e);
        return null;
    }
}
// Admin Filtreleme
let selectedTicketForAssignment = null;

document.addEventListener("DOMContentLoaded", () => {
    const adminFilterBtn = document.getElementById("admin-filter-btn");
    const closeModalBtn = document.getElementById("close-modal");
    const assignForm = document.getElementById("assign-form");
    
    if (adminFilterBtn) {
        adminFilterBtn.addEventListener("click", () => {
            const deptFilter = document.getElementById("admin-dept-filter")?.value || "";
            const statusFilter = document.getElementById("admin-status-filter")?.value || "";
            loadAdminTickets(deptFilter, statusFilter);
        });
    }
    
    if (closeModalBtn) {
        closeModalBtn.addEventListener("click", () => {
            document.getElementById("assign-modal").style.display = "none";
            selectedTicketForAssignment = null;
        });
    }
    
    if (assignForm) {
        assignForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const deptName = document.getElementById("assign-department").value;
            await assignTicketToDepartment(selectedTicketForAssignment, deptName);
            document.getElementById("assign-modal").style.display = "none";
            selectedTicketForAssignment = null;
            assignForm.reset();
        });
    }
});

// Admin - Filtreleme ile Ticket'ları Yükle
async function loadAdminTickets(deptFilter = "", statusFilter = "") {
    try {
        let url = `${API_BASE_URL}/tickets/?`;
        if (deptFilter) url += `department_filter=${deptFilter}&`;
        if (statusFilter) url += `status_filter=${statusFilter}&`;
        
        const response = await fetch(url, {
            headers: { "Authorization": `Bearer ${authToken}` }
        });
        
        if (response.ok) {
            const tickets = await response.json();
            const container = document.getElementById("admin-tickets-container");
            if (!container) return;
            
            container.innerHTML = "";
            
            if (tickets.length === 0) {
                container.innerHTML = "<p>Filtreleme kriterlerine uygun ticket bulunmamaktadır.</p>";
                return;
            }
            
            tickets.forEach(ticket => {
                const ticketDiv = document.createElement("div");
                ticketDiv.className = "ticket-item";
                ticketDiv.innerHTML = `
                    <h4>${ticket.title}</h4>
                    <p><strong>Durum:</strong> <span class="status-${ticket.status.toLowerCase()}">${ticket.status}</span></p>
                    <p><strong>Öncelik:</strong> <span class="priority-${ticket.priority.toLowerCase()}">${ticket.priority}</span></p>
                    <p><strong>Açıklama:</strong> ${ticket.description}</p>
                    <p><strong>Oluşturma:</strong> ${new Date(ticket.created_at).toLocaleString('tr-TR')}</p>
                    <button class="assign-btn" data-ticket-id="${ticket.id}" style="margin-top: 10px; padding: 8px 16px; background-color: #667eea; color: white; border: none; border-radius: 5px; cursor: pointer;">Departmana Ata</button>
                `;
                container.appendChild(ticketDiv);
                
                // Departman Ata butonu
                const assignBtn = ticketDiv.querySelector(".assign-btn");
                assignBtn.addEventListener("click", () => {
                    selectedTicketForAssignment = ticket.id;
                    document.getElementById("assign-modal").style.display = "block";
                });
            });
        }
    } catch (error) {
        showMessage("Ticketler yüklenemedi!", "error");
        console.error(error);
    }
}

// Admin - Ticket'ı Departmana Ata
async function assignTicketToDepartment(ticketId, departmentName) {
    try {
        const response = await fetch(`${API_BASE_URL}/tickets/${ticketId}/assign-department?department_name=${departmentName}`, {
            method: "PUT",
            headers: { "Authorization": `Bearer ${authToken}` }
        });
        
        if (response.ok) {
            showMessage("Ticket başarıyla departmana atandı!", "success");
            loadAdminTickets();
        } else {
            const error = await response.json();
            showMessage(`Hata: ${error.detail}`, "error");
        }
    } catch (error) {
        showMessage("Atama sırasında hata oluştu!", "error");
        console.error(error);
    }
}

const API_BASE_URL = "http://localhost:8000/api/v1";
let authToken = localStorage.getItem("token");
let currentUser = localStorage.getItem("currentUser");
let currentUserRole = localStorage.getItem("userRole");

// UI Elements
const authSection = document.getElementById("auth-section");
const ticketSection = document.getElementById("ticket-section");
const messageDiv = document.getElementById("message");
const loginForm = document.getElementById("login-form");
const registerForm = document.getElementById("register-form");
const ticketForm = document.getElementById("ticket-form");
const logoutButton = document.getElementById("logout-button");
const showRegisterLink = document.getElementById("show-register");
const userInfo = document.getElementById("user-info");
const currentUserSpan = document.getElementById("current-user");
const currentUserRoleSpan = document.getElementById("current-user-role");
const ticketsContainer = document.getElementById("tickets-container");
const studentSection = document.getElementById("student-section");
const supportSection = document.getElementById("support-section");
const departmentSection = document.getElementById("department-section");
const adminSection = document.getElementById("admin-section");

// Refresh current user by calling /auth/me; fallback to decoding JWT
async function refreshCurrentUser() {
    if (!authToken) return false;
    try {
        const meResponse = await fetch(`${API_BASE_URL}/auth/me`, {
            headers: { "Authorization": `Bearer ${authToken}` }
        });
        if (meResponse.ok) {
            const userData = await meResponse.json();
            currentUser = userData.email;
            currentUserRole = userData.role?.name || currentUserRole;
            localStorage.setItem('currentUser', currentUser);
            localStorage.setItem('userRole', currentUserRole);
            return true;
        }
    } catch (e) {
        console.error('refreshCurrentUser failed', e);
    }

    // Fallback: try decode token payload
    const payload = decodeJwt(authToken);
    if (payload) {
        currentUser = payload.sub || currentUser;
        currentUserRole = payload.role || currentUserRole || 'student';
        localStorage.setItem('currentUser', currentUser);
        localStorage.setItem('userRole', currentUserRole);
        return true;
    }
    return false;
}

// Initialize app on load
window.addEventListener('load', async () => {
    if (authToken) {
        await refreshCurrentUser();
        showTicketSection();
        loadMyTickets();
        if (currentUserRole === 'admin') setTimeout(() => loadAdminTickets(), 500);
    } else {
        showAuthSection();
    }
});

// Toggle Register Form
showRegisterLink.addEventListener("click", (e) => {
    e.preventDefault();
    document.getElementById("register-title").style.display = 
        document.getElementById("register-title").style.display === "none" ? "block" : "none";
    registerForm.style.display = registerForm.style.display === "none" ? "block" : "none";
});

// Register User
registerForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const email = document.getElementById("register-email").value;
    const password = document.getElementById("register-password").value;
    const role_name = document.getElementById("register-role").value;

    try {
        const response = await fetch(`${API_BASE_URL}/auth/register`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, password, role_name })
        });

        if (response.ok) {
            showMessage("Kayıt başarılı! Lütfen giriş yapınız.", "success");
            registerForm.reset();
            setTimeout(() => {
                document.getElementById("register-title").style.display = "none";
                registerForm.style.display = "none";
            }, 1500);
        } else {
            const error = await response.json();
            showMessage(`Hata: ${error.detail}`, "error");
        }
    } catch (error) {
        showMessage("Bağlantı hatası!", "error");
        console.error(error);
    }
});

// Login User
loginForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const username = document.getElementById("login-email").value;
    const password = document.getElementById("login-password").value;

    try {
        const response = await fetch(`${API_BASE_URL}/auth/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username, password })
        });

        if (response.ok) {
            const data = await response.json();
            authToken = data.access_token;
            currentUser = username;
            
            // Rol bilgisini al (önce API, olmazsa token payload'ından al)
            try {
                const meResponse = await fetch(`${API_BASE_URL}/auth/me`, {
                    headers: { "Authorization": `Bearer ${authToken}` }
                });

                if (meResponse.ok) {
                    const userData = await meResponse.json();
                    currentUserRole = userData.role?.name || 'student';
                    localStorage.setItem("userRole", currentUserRole);
                } else {
                    const payload = decodeJwt(authToken);
                    currentUserRole = payload?.role || 'student';
                    localStorage.setItem("userRole", currentUserRole);
                }
            } catch (e) {
                console.error("Kullanıcı bilgisi alınamadı:", e);
                const payload = decodeJwt(authToken);
                currentUserRole = payload?.role || 'student';
                localStorage.setItem("userRole", currentUserRole);
            }
            
            localStorage.setItem("token", authToken);
            localStorage.setItem("currentUser", currentUser);
            showMessage("Giriş başarılı!", "success");
            loginForm.reset();
            showTicketSection();
            loadMyTickets();
        } else {
            const error = await response.json();
            showMessage("Hatalı e-posta veya şifre!", "error");
        }
    } catch (error) {
        showMessage("Bağlantı hatası!", "error");
        console.error(error);
    }
});

// Create Ticket
ticketForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const title = document.getElementById("ticket-title").value;
    const description = document.getElementById("ticket-description").value;
    const department_name = document.getElementById("ticket-department").value;
    const priority = document.getElementById("ticket-priority").value;

    try {
        const response = await fetch(`${API_BASE_URL}/tickets/`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${authToken}`
            },
            body: JSON.stringify({ title, description, department_name, priority })
        });

        if (response.ok) {
            showMessage("Ticket başarıyla oluşturuldu!", "success");
            ticketForm.reset();
            loadMyTickets();
        } else {
            const error = await response.json();
            showMessage(`Hata: ${error.detail || "Bilinmeyen hata"}`, "error");
        }
    } catch (error) {
        showMessage("Ticket oluşturulamadı!", "error");
        console.error(error);
    }
});

// Load My Tickets
async function loadMyTickets() {
    try {
        let endpoint = `${API_BASE_URL}/tickets/my`;
        let containerId = "tickets-container";
        
        // Rol bazlı endpoint seçimi
        if (currentUserRole === "support") {
            endpoint = `${API_BASE_URL}/tickets/support`;
            containerId = "support-tickets-container";
        } else if (currentUserRole === "department") {
            endpoint = `${API_BASE_URL}/tickets/department`;
            containerId = "department-tickets-container";
        } else if (currentUserRole === "admin") {
            endpoint = `${API_BASE_URL}/tickets/`;
            containerId = "admin-tickets-container";
        }

        const response = await fetch(endpoint, {
            headers: {
                "Authorization": `Bearer ${authToken}`
            }
        });

        if (response.ok) {
            const tickets = await response.json();
            const container = document.getElementById(containerId);
            if (!container) return;
            
            container.innerHTML = "";

            if (tickets.length === 0) {
                container.innerHTML = "<p>Ticket bulunmamaktadır.</p>";
                return;
            }

            tickets.forEach(ticket => {
                const ticketDiv = document.createElement("div");
                ticketDiv.className = "ticket-item";
                ticketDiv.innerHTML = `
                    <h4>${ticket.title}</h4>
                    <p><strong>Durum:</strong> <span class="status-${ticket.status.toLowerCase()}">${ticket.status}</span></p>
                    <p><strong>Öncelik:</strong> <span class="priority-${ticket.priority.toLowerCase()}">${ticket.priority}</span></p>
                    <p><strong>Açıklama:</strong> ${ticket.description}</p>
                    <p><strong>Oluşturma:</strong> ${new Date(ticket.created_at).toLocaleString('tr-TR')}</p>
                    <div id="comments-${ticket.id}"></div>
                    <form class="comment-form" data-ticket-id="${ticket.id}">
                        <input type="text" placeholder="Yorum yazın..." required>
                        <button type="submit">Yorum Ekle</button>
                    </form>
                `;
                container.appendChild(ticketDiv);

                // Load Comments
                loadComments(ticket.id);

                // Add comment listener
                const commentForm = ticketDiv.querySelector(".comment-form");
                commentForm.addEventListener("submit", (e) => addComment(e, ticket.id));
            });
        } else {
            showMessage("Ticketler yüklenemedi!", "error");
        }
    } catch (error) {
        showMessage("Bağlantı hatası!", "error");
        console.error(error);
    }
}

// Load Comments
async function loadComments(ticketId) {
    try {
        // Bu endpoint yoksa, ticket detayından comment çek
        const tickets = document.querySelectorAll(".ticket-item");
        tickets.forEach(t => {
            // Comments already loaded from main fetch
        });
    } catch (error) {
        console.error("Yorumlar yüklenemedi:", error);
    }
}

// Add Comment
async function addComment(e, ticketId) {
    e.preventDefault();
    const content = e.target.querySelector("input").value;

    try {
        const response = await fetch(`${API_BASE_URL}/tickets/${ticketId}/comment`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${authToken}`
            },
            body: JSON.stringify({ content })
        });

        if (response.ok) {
            e.target.reset();
            loadMyTickets(); // Refresh all
            showMessage("Yorum eklendi!", "success");
        } else {
            showMessage("Yorum eklenemedi!", "error");
        }
    } catch (error) {
        showMessage("Yorum gönderirken hata oluştu!", "error");
        console.error(error);
    }
}

// Logout
logoutButton.addEventListener("click", () => {
    localStorage.removeItem("token");
    localStorage.removeItem("currentUser");
    localStorage.removeItem("userRole");
    authToken = null;
    currentUser = null;
    currentUserRole = null;
    showAuthSection();
    loginForm.reset();
    registerForm.reset();
    showMessage("Çıkış yapıldı.", "success");
});

// Helper Functions
function showMessage(text, type) {
    messageDiv.textContent = text;
    messageDiv.className = type === "success" ? "message success" : "message error";
    messageDiv.classList.remove("hidden");
    setTimeout(() => {
        messageDiv.classList.add("hidden");
    }, 3000);
}

function showAuthSection() {
    authSection.style.display = "block";
    ticketSection.style.display = "none";
    userInfo.style.display = "none";
}

function showTicketSection() {
    authSection.style.display = "none";
    ticketSection.style.display = "block";
    userInfo.style.display = "block";
    currentUserSpan.textContent = currentUser || "Kullanıcı";
    
    // Rol label'ını göster
    const roleLabel = getRoleLabel(currentUserRole);
    if (currentUserRoleSpan) {
        currentUserRoleSpan.textContent = roleLabel;
    }
    
    // Rol bazlı section gösterilmesi
    if (studentSection) studentSection.style.display = (currentUserRole === "student") ? "block" : "none";
    if (supportSection) supportSection.style.display = (currentUserRole === "support") ? "block" : "none";
    if (departmentSection) departmentSection.style.display = (currentUserRole === "department") ? "block" : "none";
    if (adminSection) adminSection.style.display = (currentUserRole === "admin") ? "block" : "none";
    
    // Support ve department için ticket listesini yükle
    if (currentUserRole === "support" || currentUserRole === "department" || currentUserRole === "admin") {
        loadMyTickets();
    }
}

function getRoleLabel(role) {
    const roleLabels = {
        "student": "Öğrenci",
        "support": "Destek Personeli",
        "department": "Departman Yöneticisi",
        "admin": "Yönetici"
    };
    return roleLabels[role] || role;
}
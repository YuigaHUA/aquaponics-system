// User management page handles account list, form save and delete operations.
(function () {
    const endpoints = window.USER_ENDPOINTS;
    const api = window.AppApi;
    const utils = window.AppUtils;

    const alertContainer = document.getElementById("userAlert");
    const tableBody = document.getElementById("usersTableBody");
    const modalElement = document.getElementById("userFormModal");
    const userModal = new bootstrap.Modal(modalElement);
    const form = document.getElementById("userForm");
    const title = document.getElementById("userFormTitle");
    const fields = {
        id: document.getElementById("userId"),
        username: document.getElementById("username"),
        displayName: document.getElementById("displayName"),
        password: document.getElementById("password"),
    };

    let users = [];

    function showAlert(message, level) {
        alertContainer.innerHTML = `
            <div class="alert alert-${level} alert-dismissible fade show" role="alert">
                ${utils.escapeHtml(message)}
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            </div>
        `;
    }

    function userUrl(id) {
        return endpoints.userUrlTemplate.replace("__USER__", id);
    }

    function openForm(user) {
        form.reset();
        fields.id.value = user ? user.id : "";
        fields.username.value = user ? user.username : "";
        fields.displayName.value = user ? user.display_name : "";
        fields.password.required = !user;
        title.textContent = user ? "Edit User" : "Add User";
        userModal.show();
    }

    function renderTable() {
        if (!users.length) {
            tableBody.innerHTML = '<tr><td colspan="4" class="text-center text-body-secondary">No users available</td></tr>';
            return;
        }
        tableBody.innerHTML = users.map((user) => `
            <tr>
                <td>${utils.escapeHtml(user.username)}</td>
                <td>${utils.escapeHtml(user.display_name)}</td>
                <td>${utils.formatDateTime(user.created_at)}</td>
                <td class="text-end">
                    <button type="button" class="btn btn-sm btn-outline-primary" data-edit-user="${user.id}">Edit</button>
                    <button type="button" class="btn btn-sm btn-outline-danger" data-delete-user="${user.id}">Delete</button>
                </td>
            </tr>
        `).join("");

        tableBody.querySelectorAll("[data-edit-user]").forEach((button) => {
            button.addEventListener("click", function () {
                const user = users.find((item) => String(item.id) === String(button.dataset.editUser));
                openForm(user);
            });
        });
        tableBody.querySelectorAll("[data-delete-user]").forEach((button) => {
            button.addEventListener("click", async function () {
                if (!window.confirm("Confirm delete this user?")) {
                    return;
                }
                try {
                    await api.deleteJson(userUrl(button.dataset.deleteUser));
                    showAlert("User deleted", "success");
                    await loadUsers();
                } catch (error) {
                    showAlert(error.message, "danger");
                }
            });
        });
    }

    async function loadUsers() {
        users = await api.getJson(endpoints.usersUrl);
        renderTable();
    }

    document.getElementById("addUserButton").addEventListener("click", function () {
        openForm(null);
    });

    form.addEventListener("submit", async function (event) {
        event.preventDefault();
        const payload = {
            username: fields.username.value,
            display_name: fields.displayName.value,
            password: fields.password.value,
        };
        try {
            if (fields.id.value) {
                await api.putJson(userUrl(fields.id.value), payload);
                showAlert("User updated", "success");
            } else {
                await api.postJson(endpoints.usersUrl, payload);
                showAlert("User created", "success");
            }
            userModal.hide();
            await loadUsers();
        } catch (error) {
            showAlert(error.message, "danger");
        }
    });

    loadUsers().catch((error) => showAlert(error.message, "danger"));
})();

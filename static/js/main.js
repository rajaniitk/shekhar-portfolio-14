document.addEventListener('DOMContentLoaded', () => {
    const sidebarToggleBtn = document.getElementById('sidebar-toggle-btn');
    const sidebar = document.getElementById('sidebar');
    const sidebarCloseBtn = document.getElementById('sidebar-close-btn');
    const mainContent = document.getElementById('main-content');

    // Function to toggle sidebar visibility and update main content padding
    function toggleSidebar() {
        const isHidden = sidebar.classList.contains('hidden');

        sidebar.classList.toggle('hidden');
        mainContent.classList.toggle('sidebar-hidden');

        // Optional: Update hamburger icon appearance if needed
        // if (isHidden) {
        //     sidebarToggleBtn.innerHTML = '&#10799;'; // Example: 'X' or another icon
        // } else {
        //     sidebarToggleBtn.innerHTML = '&#9776;'; // Hamburger icon
        // }
    }

    // Event listener for the hamburger button (always on)
    if (sidebarToggleBtn) {
        sidebarToggleBtn.addEventListener('click', (event) => {
            event.stopPropagation(); // Prevent document click from closing immediately
            toggleSidebar();
        });
    }

    // Event listener for the close button inside the sidebar
    if (sidebarCloseBtn) {
        sidebarCloseBtn.addEventListener('click', () => {
            sidebar.classList.add('hidden');
            mainContent.classList.add('sidebar-hidden');
        });
    }

    // Close sidebar when clicking outside of it
    document.addEventListener('click', (event) => {
        // Only proceed if the sidebar is currently NOT hidden
        if (!sidebar.classList.contains('hidden')) {
            // Check if the click was outside the sidebar AND outside the toggle button
            if (!sidebar.contains(event.target) && !sidebarToggleBtn.contains(event.target)) {
                sidebar.classList.add('hidden');
                mainContent.classList.add('sidebar-hidden');
            }
        }
    });

    // Highlight the active link in the sidebar
    const currentPath = window.location.pathname.replace(/\/$/, ''); // Remove trailing slash for comparison
    const sidebarLinks = document.querySelectorAll('.sidebar-menu a');
    sidebarLinks.forEach(link => {
        const linkHref = link.getAttribute('href').replace(/\/$/, '');

        if (currentPath === '' && linkHref === '') { // Matches root path '/'
             link.classList.add('active');
        } else if (currentPath !== '' && linkHref === currentPath) { // Matches other paths
             link.classList.add('active');
        }
    });

    // Initial setup: Ensure correct state on page load for mobile (sidebar starts hidden)
    const mobileMediaQuery = window.matchMedia('(max-width: 768px)');
    if (mobileMediaQuery.matches) {
        // On mobile, ensure sidebar starts hidden and content has no padding
        sidebar.classList.add('hidden');
        mainContent.classList.add('sidebar-hidden');
    }

    // Add listener for window resize to adjust sidebar state if needed
    mobileMediaQuery.addEventListener('change', (event) => {
        if (event.matches) { // Matches means screen is now SMALLER than 768px
            // Ensure sidebar is hidden and content has no padding
            if (!sidebar.classList.contains('hidden')) {
                sidebar.classList.add('hidden');
                mainContent.classList.add('sidebar-hidden');
            }
        } else { // Does not match means screen is now LARGER than 768px
            // Ensure sidebar is visible and content has padding
            if (sidebar.classList.contains('hidden')) {
                sidebar.classList.remove('hidden');
                mainContent.classList.remove('sidebar-hidden');
            }
        }
    });
});
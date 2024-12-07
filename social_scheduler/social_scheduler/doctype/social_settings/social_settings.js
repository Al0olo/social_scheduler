frappe.ui.form.on('Social Settings', {
    refresh: function(frm) {
        frm.add_custom_button('Connect LinkedIn', () => {
            frappe.call({
                method: 'social_scheduler.social_scheduler.oauth.get_linkedin_auth_url',
                callback: function(response) {
                    window.open(response.message, '_blank', 'width=800,height=600');
                }
            });
        });

        frm.add_custom_button('Connect Twitter', () => {
            frappe.call({
                method: 'social_scheduler.social_scheduler.oauth.get_twitter_auth_url',
                callback: function(response) {
                    window.open(response.message, '_blank', 'width=800,height=600');
                }
            });
        });
    }
});
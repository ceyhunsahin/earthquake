window.dashExtensions = Object.assign({}, window.dashExtensions, {
    default: {
        function0: function(feature, context) {
            const match = context.props.hideout && context.props.hideout.properties.name === feature.properties.name;
            if (match) return {
                weight: 5,
                color: '#666',
                dashArray: ''
            };
        }
    }
});
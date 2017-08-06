schedule:
  update_test_config:
    function: state.sls
    args:
      - router.ntp
    hours: 1
    splay: 1

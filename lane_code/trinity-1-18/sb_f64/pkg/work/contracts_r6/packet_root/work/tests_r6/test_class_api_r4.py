from trace_format.contracts import contract_epoch, epoch_class


def test_epoch_class_static_api_and_super():
    class Sealed:
        marker='OFF'
        def value(self):return self.marker
    class Current:
        marker='ON'
        def value(self):return self.marker
    Shared=epoch_class(Sealed,Current)
    class Provider(Shared):
        def value(self):return super().value()+' subclass'
    for enabled in (False,True,False):
        with contract_epoch(enabled):
            expected='ON' if enabled else 'OFF'
            assert Shared.marker==Provider.marker==expected
            instance=Provider()
            assert isinstance(instance,Provider)
            assert instance.value()==expected+' subclass'

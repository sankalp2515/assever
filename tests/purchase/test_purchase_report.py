import pytest
from intentseal_core.delegate.receipts import Sentence, chain_hash, write_report


@pytest.mark.asyncio
async def test_purchase_report_preserves_provider_amount_with_model_writer():
    class MisleadingWriter:
        name='synthetic-model'
        async def write(self, request, receipts):
            pytest.fail('Financial purchase receipts must use typed provider facts')
            return [Sentence('The purchase may have completed.', ['R-2'])]

    receipts=[{'rid':'R-2','kind':'purchase_effect','data':{
        'purchase_event_kind':'CONFIRMED','effect':{'total_paise':70000}}}]
    receipts[0]['prev']=''
    receipts[0]['hash']=chain_hash('',receipts[0])
    result=await write_report('Buy the approved basket.',receipts,writer=MisleadingWriter())
    assert result['writer']=='template'
    assert result['chain_ok']
    assert result['sentences']==[{'text':'The provider confirmed the approved purchase; gross amount ₹700.00.','cites':['R-2']}]

import {describe,expect,it} from 'vitest'
import {STATUS_COLORS,STATUS_ORDER} from './tokens'
describe('token status',()=>{it('mendefinisikan empat status utama sekali',()=>{expect(STATUS_ORDER).toHaveLength(4);STATUS_ORDER.forEach(x=>expect(STATUS_COLORS[x]).toBeTruthy())})})

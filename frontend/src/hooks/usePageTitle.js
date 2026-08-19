import {useEffect} from 'react'

export function usePageTitle(title){
  useEffect(()=>{
    if(title===undefined)return
    document.title=title||'SEBATIK'
  },[title])
}

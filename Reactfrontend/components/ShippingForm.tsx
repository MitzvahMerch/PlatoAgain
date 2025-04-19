// ReactFrontend/components/ShippingForm.tsx
import React, { useState, useEffect, useRef, FormEvent } from 'react';
import { chatPermissions } from '../lib/chatPermissions';
import { trackEvent } from '../lib/googleAnalytics';

export interface ShippingFormData {
  fullName: string;
  address: string;
  email: string;
  receiveDate: string;
}

interface ShippingFormProps {
  orderDetails: Record<string, any>;
  onCancel: () => void;
  onSubmit: (data: ShippingFormData) => void;
}

const ShippingForm: React.FC<ShippingFormProps> = ({ orderDetails, onCancel, onSubmit }) => {
  // Form state
  const [fullName, setFullName] = useState('');
  const [address, setAddress] = useState('');
  const [email, setEmail] = useState('');
  const [receiveDate, setReceiveDate] = useState('');
  const [errors, setErrors] = useState<Partial<ShippingFormData>>({});
  
  // Address suggestions state
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const addressRef = useRef<HTMLInputElement>(null);

  // Calendar state
  const [showCalendar, setShowCalendar] = useState(false);
  const [currentMonth, setCurrentMonth] = useState(new Date());
  const [selectedDateObj, setSelectedDateObj] = useState<Date | null>(null);

  // Inject original custom CSS on mount
  useEffect(() => {
    const styleElement = document.createElement('style');
    styleElement.textContent = `
      /* original shipping-form-in-chat injected styles */
      .shipping-form-container { margin-top:15px; padding-top:15px; border-top:1px solid rgba(255,255,255,0.2); width:100%; }
      .shipping-form-header { margin:0 0 15px 0; font-size:16px; color:var(--secondary-color); font-weight:500; text-align:center; }
      .shipping-form-group { margin-bottom:15px; position:relative; }
      .shipping-form-label { display:block; margin-bottom:5px; font-weight:bold; color:white; font-size:14px; }
      .shipping-form-input { width:100%; padding:10px; border:1px solid rgba(255,255,255,0.3); border-radius:4px; font-size:14px; background:rgba(255,255,255,0.1); color:white; }
      .shipping-form-input:focus { outline:none; border-color:var(--primary-color); }
      .date-picker-container { position:absolute; width:320px; background:#333; border:1px solid rgba(255,255,255,0.3); border-radius:4px; z-index:2050; box-shadow:0 4px 6px rgba(0,0,0,0.3); padding:10px; color:white; }
      .address-suggestions { position:absolute; width:100%; background:#333; border:1px solid rgba(255,255,255,0.3); border-top:none; border-radius:0 0 4px 4px; z-index:2050; max-height:200px; overflow-y:auto; box-shadow:0 4px 6px rgba(0,0,0,0.3); }
      .suggestion-item { padding:10px; cursor:pointer; border-bottom:1px solid rgba(255,255,255,0.1); color:white; }
      .suggestion-item:hover { background:rgba(255,255,255,0.1); }
    `;
    document.head.appendChild(styleElement);
    return () => { document.head.removeChild(styleElement); };
  }, []);

  // Disable chat when form is open
  useEffect(() => {
    chatPermissions.disableChat('Please complete your order information');
    return () => { chatPermissions.enableChat(); };
  }, []);

  // Manual address autocomplete fetch
  useEffect(() => {
    const input = addressRef.current!;
    let timer: NodeJS.Timeout;

    const onInput = () => {
      clearTimeout(timer);
      const val = input.value;
      if (val.length < 3) { setShowSuggestions(false); return; }
      timer = setTimeout(async () => {
        try {
          const res = await fetch('https://places.googleapis.com/v1/places:autocomplete', {
            method:'POST',
            headers:{ 'Content-Type':'application/json', 'X-Goog-Api-Key': process.env.NEXT_PUBLIC_GOOGLE_PLACES_API_KEY! },
            body: JSON.stringify({ input: val })
          });
          const data = await res.json();
          const texts = (data.suggestions||[]).map((s:any)=>s.placePrediction.text.text);
          setSuggestions(texts);
          setShowSuggestions(texts.length>0);
        } catch{ setShowSuggestions(false); }
      }, 300);
    };
    input.addEventListener('input', onInput);
    return () => { input.removeEventListener('input', onInput); };
  }, []);

  // Calendar helper functions (tiers, rendering)
  const getStandardizedDates = () => {
    const todayET = new Date(new Date().toLocaleString('en-US',{ timeZone:'America/New_York' }));
    todayET.setHours(0,0,0,0);
    const freeDate = new Date(todayET);
    freeDate.setDate(freeDate.getDate()+17);
    return { today: todayET, freeDate };
  };

  const { today, freeDate } = getStandardizedDates();

  const isDateDisabled = (d: Date) => {
    const dt = new Date(d); dt.setHours(0,0,0,0);
    return dt < today;
  };

  const handleDateClick = (d: Date) => {
    setSelectedDateObj(d);
    setReceiveDate(d.toLocaleDateString('en-US'));
    setShowCalendar(false);
  };

  const changeMonth = (offset: number) => {
    const m = new Date(currentMonth);
    m.setMonth(m.getMonth()+offset);
    setCurrentMonth(m);
  };

  // Form validation
  const validate = (): boolean => {
    const errs:Partial<ShippingFormData> = {};
    if(!fullName.trim()) errs.fullName='Required';
    if(!address.trim()) errs.address='Required';
    if(!email.match(/^[^\s@]+@[^\s@]+\.[^\s@]+$/)) errs.email='Valid email required';
    if(!receiveDate) errs.receiveDate='Required';
    setErrors(errs);
    return Object.keys(errs).length===0;
  };

  const handleSubmit = (e:FormEvent) => {
    e.preventDefault();
    if(!validate()) return;
    trackEvent('complete_shipping_form',{ full_name:fullName,email,receive_date:receiveDate,...orderDetails });
    chatPermissions.enableChat();
    onSubmit({ fullName,address,email,receiveDate });
  };

  return (
    <div className="shipping-form-container">
      <div className="shipping-form-header">Complete Your Order</div>
      <form onSubmit={handleSubmit} className="shipping-form">
        <div className="shipping-form-group">
          <label className="shipping-form-label" htmlFor="name">Full Name</label>
          <input id="name" className="shipping-form-input" value={fullName} onChange={e=>setFullName(e.target.value)} />
          {errors.fullName && <div className="text-red-400">{errors.fullName}</div>}
        </div>

        <div className="shipping-form-group">
          <label className="shipping-form-label" htmlFor="address">Shipping Address</label>
          <input id="address" ref={addressRef} className="shipping-form-input" value={address} onChange={e=>setAddress(e.target.value)} />
          {showSuggestions && (
            <div className="address-suggestions">
              {suggestions.map((txt,i)=><div key={i} className="suggestion-item" onClick={()=>{setAddress(txt);setShowSuggestions(false);}}>{txt}</div>)}
            </div>
          )}
          {errors.address && <div className="text-red-400">{errors.address}</div>}
        </div>

        <div className="shipping-form-group">
          <label className="shipping-form-label" htmlFor="email">Email for Invoice</label>
          <input id="email" type="email" className="shipping-form-input" value={email} onChange={e=>setEmail(e.target.value)} />
          {errors.email && <div className="text-red-400">{errors.email}</div>}
        </div>

        <div className="shipping-form-group" style={{ position:'relative' }}>
          <label className="shipping-form-label" htmlFor="recv-date">Receive By Date</label>
          <input id="recv-date" readOnly className="shipping-form-input" value={receiveDate} onClick={()=>setShowCalendar(v=>!v)} />
          {showCalendar && (
            <div className="date-picker-container">
              <div className="flex justify-between items-center mb-2">
                <button type="button" onClick={()=>changeMonth(-1)}>&lt;</button>
                <span>{currentMonth.toLocaleString('default',{ month:'long', year:'numeric' })}</span>
                <button type="button" onClick={()=>changeMonth(1)}>&gt;</button>
              </div>
              <div className="grid grid-cols-7 text-xs mb-1">
                {['Su','Mo','Tu','We','Th','Fr','Sa'].map(d=><div key={d}>{d}</div>)}
              </div>
              <div className="grid grid-cols-7 gap-1">
                {(() => {
                  const first = new Date(currentMonth.getFullYear(),currentMonth.getMonth(),1);
                  const start = first.getDay();
                  const days = new Date(currentMonth.getFullYear(),currentMonth.getMonth()+1,0).getDate();
                  const cells = [];
                  for(let i=0;i<start;i++) cells.push(<div key={'b'+i} className="text-gray-500"> </div>);
                  for(let d=1;d<=days;d++){
                    const dt=new Date(currentMonth.getFullYear(),currentMonth.getMonth(),d);
                    const disabled = isDateDisabled(dt);
                    cells.push(
                      <div key={d} className={`p-1 text-center cursor-pointer ${disabled?'text-gray-500 pointer-events-none':'hover:bg-gray-700'}`} onClick={()=>handleDateClick(dt)}>
                        {d}
                      </div>
                    );
                  }
                  return cells;
                })()}
              </div>
            </div>
          )}
          {errors.receiveDate && <div className="text-red-400">{errors.receiveDate}</div>}
        </div>

        <div className="flex justify-end space-x-2 mt-4 pt-4 border-t border-gray-600">
          <button type="button" className="px-4 py-2" onClick={()=>{chatPermissions.enableChat();onCancel();}}>Cancel</button>
          <button type="submit" className="px-4 py-2 bg-[var(--primary-color)] text-white">Complete Order</button>
        </div>
      </form>
    </div>
  );
};

export default ShippingForm;
